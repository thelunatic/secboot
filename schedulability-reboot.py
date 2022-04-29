import math
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import random
import statistics as stat
import json
import time
from progressbar import progressbar as progress
from progressbar import ProgressBar as pbar
import progressbar
import csv
import sys
import matplotlib.tri as tri

fontsize = 20

'''
steps:
    * Generate task sets as per utilisation
    * For each task set:
      * calculate percentage of tasks schedulable in normal system
      * calculate percentage of tasks schedulable with reboot
'''

def UUniFast(n, U, tr):
    '''
    Implementation of UUnifast algorithm following the original paper.
    '''
    vec = []
    sumU = U
    for i in range(0, n):
        nextsumU = sumU*np.random.uniform(1/(n-i))
        vec.append(sumU - nextsumU)
        sumU = nextsumU
    vec[n-1] = sumU

    return vec

def task_generator(n, u, h, e, tr):
    '''
    Input:
        number of tasks
        total system utilization
        fixed hyperperiod
        reboot time or system unavailability time (epsilon)
        reboot period (T_r)

    Output:
        a tuple (c, t, factors) where:
            c -> list of WCET
            t -> list of periods
            factor -> factors of h
    '''
    utils = UUniFast(n, u, tr)
    t = []
    c = []
    factors = [i for i in range(1, h+1) if h%i == 0]

    for util in utils:
        if util > 0:
            p = random.choice(factors)
        else:
            p = 0
        t.append(p)
        c.append(util*p)

    return (c, t, factors)

def steady_ri(c, t, i):
    r = [c[i]]
    n = 0

    while(1):
        i_hp = 0

        for j in range(i):
            if t[j] > 0:
                i_hp += math.ceil(r[n]/t[j])*c[j]

        r.append(c[i] + i_hp)
        n = n+1

        if(r[n] == r[n-1] or r[n] > t[i]):
            break;
    return r[n]

def reboot_ri(c, t, i, e):
    r = [c[i]]
    n = 0

    while(1):
        i_hp = 0

        for j in range(i):
            if t[j] > 0:
                i_hp += math.ceil(r[n]/t[j])*c[j]

        r.append(e + c[i] + i_hp)
        n = n+1

        if(r[n] == r[n-1] or r[n] > t[i]):
            break;
    return r[n]

def schedulability(n, c, t, u, h, tr, e):
    sched_list = np.zeros(n)

    if tr == 0:
        for i in range(n):
            r = steady_ri(c, t, i) 
            if r <= t[i]:
                sched_list [i] = 1

    else:
        if u + e/tr > 1:
            return 0
        for i in range(n):
            dist = [t[i]]
            r = reboot_ri(c, t, i, e)

            if r > t[i]:
                continue
            if r > tr:
                continue
            for k in range(1, int(h/tr)+1):
                if k*tr%t[i] != 0:
                    dist.append(k*tr - math.floor(k*tr/t[i])*t[i])
            if min(dist) >= r:
                sched_list[i] = 1

    sched_percent = sum(sched_list)/n

    return sched_percent*100

def experiment1():
    '''
    Compares schedulability on 1000 random tasks for each utilization level
    fxed tr
    fixed e
    fixed h
    fixed n
    variable u
    '''
    e = 5.05
    over = 0.02856
    #e_ = 5
    n = 20
    h = 1000
    x = []
    ys = []
    #yr = [[] for _ in range(10)]
    yr = []
    yrn = []
    #tr = random.randint(e, h)
    tr = 120
    prog_bar = 0
    bar = pbar(max_value=9)

    for u in np.arange (0.1, 1, 0.1):
        u = round(u, 1)
        sched_steady = []
        sched_reboot = []
        sched_reboot_normal = []
        for _ in range(1000):
            c, t, factors = task_generator(n, u, h, e, tr)
          #  for idx in range(10):
          #      over = 1 + round((idx+1)/100, 2)
            sched_reboot.append(schedulability(n, c, t, u, h, tr, e + over))
            sched_reboot_normal.append(schedulability(n, c, t, u, h, tr, e))
            sched_steady.append(schedulability(n, c, t, u, h, 0, e))
        prog_bar += 1
        bar.update(prog_bar)
        yr.append(stat.mean(sched_reboot))
        yrn.append(stat.mean(sched_reboot_normal))
        ys.append(stat.mean(sched_steady))

        x.append(u)

    with open('exp1.csv', 'w') as fn:
        writer = csv.writer(fn)
        writer.writerow(['Utilization', 'non-reboot sched', 'secboot sched', 'normalReboot'])
        for i in range(len(x)):
            writer.writerow([x[i], ys[i], yr[i], yrn[i]])
    plt.plot(x, yr, 'v-', label='SecureReboot', fillstyle='none', markerfacecolor='none')
    plt.plot(x, yrn, 's-', label='NormalReboot', fillstyle='none', markerfacecolor='none')
    plt.plot(x, ys, 'o-', label='NonReboot', fillstyle='none')
    plt.xlabel('System utilization', fontsize=fontsize)
    plt.ylabel('Percentage of schedulable tasks', fontsize=fontsize)
    #plt.yscale('log')
    plt.xlim(0.1, 0.9)
    plt.xticks([round(i,1) for i in np.arange(0.1, 1, 0.1)] , fontsize=fontsize)
    plt.ylim(0, 100)
    #plt.yticks(fontsize=fontsize)
    plt.yticks([_*10 for _ in range(11)], fontsize=fontsize)
    plt.legend(fontsize=fontsize)
    plt.rcParams.update({'font.size':20})
    plt.tight_layout()
    plt.savefig('AFPP_sched_n{}_h{}_tr{}.eps'.format(n,h,tr), format='eps')
    plt.show()

def task_gen_handler(n, N, h, e, tr):
    '''
    generates N number of tasksets, each with n tasks
    '''
    filename='task.json'
    total = 0
    task_dict = {'tasks':[]}

    progress_var = 0

    bar = pbar(max_value=900*10)

    for u in np.arange(0.1, 1, 0.1):
        u = round(u, 1)
        total = 0
        while(total < N):
            c, t, factors = task_generator(n, u, h, e, tr)
            if (schedulability(n, c, t, u, h, 0, e) == 1):
                task_dict['tasks'].append((u,c,t,factors))
                total += 1
                progress_var += 1
                bar.update(progress_var)

    with open(filename, 'w') as fn:
        json.dump(json.dumps(task_dict), fn)

    return task_dict


def experiment2(filename='task.json'):
    '''
    Plots schedulability with restart for tasks that are 100% schedulable
    without restart.
    plots in a monte carlo fashion
    '''
    e = 5
    n = 20
    h = 1000
    x = []
    ys = []
    yr = []
    #tr = 120
    sched = {}


    with open(filename, 'r') as fn:
        tasksets = json.loads(json.load(fn))

    for tr in progress([0, 1000]):
        x = []
        yr = []
        for i in np.arange(0.1, 1, 0.1):
            i = round(i, 1)
            sched.update({i: []})

        for task in tasksets['tasks']:
            u, c, t, fact = task
            sched[u].append(schedulability(n, c, t, u, h, tr, e))

        for i in np.arange(0.1, 1, 0.1):
            i = round(i, 1)
            yr.append(stat.mean(sched[i]))
            x.append(i)

        plt.plot(x, yr, label=str(tr)) #, label='secboot')

    plt.xlabel('System utilization')
    plt.ylabel('Percentage of schedulable tasks')
    plt.legend()
    plt.show()

def experiment3():
    '''
    Random task schedulability monte carlo with fixed tr
    '''
    e = 5
    n = 20
    h = 1000
    x = []
    ys = []
    s_counter = 0
    yr = []
    #tr = random.randint(e, h)
    tr = 120
    prog_bar = 0
    bar = pbar(max_value=1000)

    for _ in range(1000):
        sched_steady = [0 for _ in range(9)]
        sched_reboot = []
        x = []
        s_counter = 0
        for u in np.arange (0.1, 1, 0.1):
            u = round(u, 1)
            c, t, factors = task_generator(n, u, h, e, tr)
            sched_reboot.append(schedulability(n, c, t, u, h, tr, e))
            sched_steady[s_counter] += schedulability(n, c, t, u, h, 0, e)
            x.append(u)
            s_counter += 1
        plt.plot(x, sched_reboot)
        prog_bar += 1
        bar.update(prog_bar)
        #yr.append(stat.mean(sched_reboot))
    ys = [blah/1000 for blah in sched_steady]

    #with open('exp1.csv', 'w') as fn:
    #    writer = csv.writer(fn)
    #    writer.writerow(['Utilization', 'non-secboot sched', 'secboot sched'])
    #    for i in range(len(x)):
    #        writer.writerow([x[i], ys[i], yr[i]])
    plt.plot(x, ys, label='non-secboot')
    plt.xlabel('System utilization')
    plt.ylabel('Percentage of schedulable tasks')
    #plt.yscale('log')
    plt.xlim(0.1, 0.9)
    plt.yticks([_*10 for _ in range(11)])
    plt.show()

def experiment4(filename='task.json'):
    '''
    monte carlo with fixed tr on schedulable tasks
    '''
    e = 5
    n = 20
    h = 1000
    x = []
    ys = []
    yr = []
    tr = 120
    sched = {}


    with open(filename, 'r') as fn:
        tasksets = json.loads(json.load(fn))

    x = []
    yr = []
    for i in np.arange(0.1, 1, 0.1):
        i = round(i, 1)
        sched.update({i: []})

    for task in tasksets['tasks']:
        u, c, t, fact = task
        sched[u].append(schedulability(n, c, t, u, h, tr, e))

    for i in range(len(sched[0.1])):
        yr = []
        x = []
        for j in np.arange(0.1, 1, 0.1):
            j = round(j, 1)
            yr.append(sched[j][i])
            x.append(j)
        plt.plot(x, yr) #, label='secboot')


    plt.xlabel('System utilization')
    plt.ylabel('Percentage of schedulable tasks')
    #plt.legend()
    plt.xlim(0.1, 0.9)
    plt.yticks([_*10 for _ in range(11)])
    plt.show()

def experiment5():
    '''
    schedulablity average on randomly generated task set with rm scheduling
    '''
    e = 5.05
    over = 0.02856
    #e_= 0.96*e
    n = 20
    h = 1000
    x = []
    ys = []
    yr = []
    yrn = []
    #tr = random.randint(e, h)
    tr = 120
    prog_bar = 0
    bar = pbar(max_value=9*10000)

    for u in np.arange (0.1, 1, 0.1):
        u = round(u, 1)
        sched_steady = []
        sched_reboot = []
        sched_reboot_normal = []
        for _ in range(10000):
            c, t, factors = task_generator(n, u, h, e, tr)
            taskset = []
            for idx in range(len(c)):
                taskset.append((t[idx], c[idx]))

            c = []
            t = []
            for task in sorted(taskset):
                c.append(task[1])
                t.append(task[0])
            
            sched_reboot.append(schedulability(n, c, t, u, h, tr, e + over))
            sched_reboot_normal.append(schedulability(n, c, t, u, h, tr, e))
            steady_temp = schedulability(n, c, t, u, h, 0, e)
            #sched_steady.append(schedulability(n, c, t, u, h, 0, e))
            sched_steady.append(steady_temp)
            prog_bar += 1
        bar.update(prog_bar)
        yr.append(stat.mean(sched_reboot))
        yrn.append(stat.mean(sched_reboot_normal))
        ys.append(stat.mean(sched_steady))

        x.append(u)

    with open('exp5.csv', 'w') as fn:
        writer = csv.writer(fn)
        writer.writerow(['Utilization', 'non-secboot sched', 'secboot sched', 'NormalReboot'])
        for i in range(len(x)):
            writer.writerow([x[i], ys[i], yr[i], yrn[i]])
    plt.plot(x, yr, 'v-', label='SecureReboot', fillstyle='none', markerfacecolor='none')
    plt.plot(x, yrn, 's-', label='NormalReboot', fillstyle='none', markerfacecolor='none')
    plt.plot(x, ys, 'o-', label='NonReboot', fillstyle='none')
    plt.xlabel('System utilization', fontsize=fontsize)
    plt.ylabel('Percentage of schedulable tasks', fontsize=fontsize)
    #plt.yscale('log')
    plt.xlim(0.1, 0.9)
    plt.xticks([round(i,1) for i in np.arange(0.1, 1, 0.1)] , fontsize=fontsize)
    plt.yticks([_*10 for _ in range(11)], fontsize=fontsize)
    plt.legend(fontsize=fontsize)
    plt.rcParams.update({'font.size':22})
    plt.tight_layout()
    plt.savefig('RM_sched_n{}_h{}_tr{}.eps'.format(n,h,tr), format='eps')
    plt.show()

def experiment6(filename='task.json'):
    '''
    Plots schedulability with restart for tasks that are 100% schedulable
    without restart.
    plots in a monte carlo fashion
    USE RM SCHEDULING 
    '''
    e = 5
    n = 20
    h = 1000
    x = []
    ys = []
    yr = []
    #tr = 120
    sched = {}


    with open(filename, 'r') as fn:
        tasksets = json.loads(json.load(fn))

    for tr in progress(range(h)):
        x = []
        yr = []
        for i in np.arange(0.1, 1, 0.1):
            i = round(i, 1)
            sched.update({i: []})

        for task in tasksets['tasks']:
            u, c, t, fact = task
            mod_taskset = []
            for idx in range(len(c)):
                mod_taskset.append((t[idx], c[idx]))

            c = []
            t = []
            for mod_task in sorted(mod_taskset):
                c.append(mod_task[1])
                t.append(mod_task[0])
            sched[u].append(schedulability(n, c, t, u, h, tr, e))

        for i in np.arange(0.1, 1, 0.1):
            i = round(i, 1)
            yr.append(stat.mean(sched[i]))
            x.append(i)

        plt.plot(x, yr, label=str(tr)) #, label='secboot')

    plt.xlabel('System utilization')
    plt.ylabel('Percentage of schedulable tasks')
    plt.legend()
    plt.show()

def experiment7():
    '''
    Variable tr 3D plot
    Compares schedulability on 1000 random tasks for each utilization level
    fixed e
    fixed h
    fixed n
    variable u
    '''
    e = 5
    e_ = 0.96*e
    n = 20
    h = 1000
    x = []
    zs = []
    zr = []
    zrn = []
    y = []
    #tr = random.randint(e, h)
    #tr = 120
    prog_bar = 0
    bar = pbar(max_value=9*h)

    for tr in range(h):
        for u in np.arange (0.1, 1, 0.1):
            u = round(u, 1)
            sched_steady = []
            sched_reboot = []
            sched_reboot_normal = []
            for _ in range(1000):
                c, t, factors = task_generator(n, u, h, e, tr)
                sched_reboot.append(schedulability(n, c, t, u, h, tr, e))
            #    sched_reboot_normal.append(schedulability(n, c, t, u, h, tr, e_))
            #    sched_steady.append(schedulability(n, c, t, u, h, 0, e))
            prog_bar += 1
            bar.update(prog_bar)
            zr.append(stat.mean(sched_reboot))
            #zrn.append(stat.mean(sched_reboot_normal))
            #zs.append(stat.mean(sched_steady))
            y.append(tr)

            x.append(u)

    #X, Z1 = np.meshgrid(x,zr)
    #Y, Z2 = np.meshgrid(y,zr)

#    with open('exp7.csv', 'w') as fn:
#        writer = csv.writer(fn)
#        writer.writerow(['Utilization', 'non-secboot sched', 'secboot sched'])
#        for i in range(len(x)):
#            writer.writerow([x[i], ys[i], yr[i], yrn[i]])

    x = np.array(x).reshape(9, h)
    y = np.array(y).reshape(9, h)
    zr = np.array(zr).reshape(9, h)
    ax = plt.axes(projection='3d')
    ax.plot_surface(x, y, zr, rstride=1, cstride=1,
                cmap='viridis', edgecolor='none')
    ax.set_xlabel('Utilization')
    ax.set_ylabel('Reboot Period (T_r)')
    ax.set_zlabel('Percentage of schedulable tasks')
    #plt.plot(x, yr, 'v-', label='SecureReboot', fillstyle='none')
    #plt.plot(x, yrn, 's-', label='NormalReboot', fillstyle='none')
    #plt.plot(x, ys, 'o-', label='NonReboot', fillstyle='none')
    #plt.xlabel('System utilization')
    #plt.ylabel('Percentage of schedulable tasks')
    ##plt.yscale('log')
    #plt.xlim(0.1, 0.9)
    #plt.yticks([_*10 for _ in range(11)])
    #plt.legend()
    plt.savefig('AFPP_var_tr_sched_n{}_h{}_tr{}.eps'.format(n,h,tr), format='eps')
    plt.show()

def experiment8():
    '''
    Variable tr 3D plot -- RM scheduling
    Compares schedulability on 1000 random tasks for each utilization level
    fixed e
    fixed h
    fixed n
    variable u
    '''
    e = 5
    e_ = 0.96*e
    n = 20
    h = 1000
    x = []
    zs = []
    zr = []
    zrn = []
    y = []
    prog_bar = 0
    bar = pbar(max_value=9*h)

    for tr in range(h):
        for u in np.arange (0.1, 1, 0.1):
            u = round(u, 1)
            sched_steady = []
            sched_reboot = []
            sched_reboot_normal = []
            for _ in range(10):
                c, t, factors = task_generator(n, u, h, e, tr)
                taskset = []
                for idx in range(len(c)):
                    taskset.append((t[idx], c[idx]))

                c = []
                t = []
                for task in sorted(taskset):
                    c.append(task[1])
                    t.append(task[0])
                sched_reboot.append(schedulability(n, c, t, u, h, tr, e))
                sched_reboot_normal.append(schedulability(n, c, t, u, h, tr, e_))
                sched_steady.append(schedulability(n, c, t, u, h, 0, e))
            prog_bar += 1
            bar.update(prog_bar)
            zr.append(stat.mean(sched_reboot))
            zrn.append(stat.mean(sched_reboot_normal))
            zs.append(stat.mean(sched_steady))
            y.append(tr)

            x.append(u)

#    with open('exp8.csv', 'w') as fn:
#        writer = csv.writer(fn)
#        writer.writerow(['Utilization', 'non-secboot sched', 'secboot sched'])
#        for i in range(len(x)):
#            writer.writerow([x[i], ys[i], yr[i], yrn[i]])

    x = np.array(x).reshape(9, h)
    y = np.array(y).reshape(9, h)
    zr = np.array(zr).reshape(9, h)
    zrn = np.array(zrn).reshape(9, h)
    zs = np.array(zs).reshape(9, h)
    ax = plt.axes(projection='3d')
    ax.plot_surface(x, y, zr, rstride=1, cstride=1,
                cmap=plt.cm.YlGnBu_r, label='SecReboot', alpha=0.2)
    ax.plot_surface(x, y, zs, rstride=1, cstride=1,
                cmap='plasma', label='NonReboot', alpha=0.2)
    ax.set_xlabel('Utilization')
    ax.set_ylabel('Reboot Period (T_r)')
    ax.set_zlabel('Percentage of schedulable tasks')
    #plt.plot(x, yr, 'v-', label='SecureReboot', fillstyle='none')
    #plt.plot(x, yrn, 's-', label='NormalReboot', fillstyle='none')
    #plt.plot(x, ys, 'o-', label='NonReboot', fillstyle='none')
    #plt.xlabel('System utilization')
    #plt.ylabel('Percentage of schedulable tasks')
    ##plt.yscale('log')
    #plt.xlim(0.1, 0.9)
    #plt.yticks([_*10 for _ in range(11)])
    #plt.legend()
    plt.savefig('RM_var_tr_sched_n{}_h{}_tr{}.eps'.format(n,h,tr), format='eps')
    plt.show()

def experiment9():
    '''
    Experiment1 with Box and whisker plot
    Compares schedulability on 1000 random tasks for each utilization level
    fxed tr
    fixed e
    fixed h
    fixed n
    variable u
    '''
    e = 5.05
    over = 0.02856
    #e = 5
    #e_ = 0.9*e
    n = 20
    h = 1000
    x = [0]
    ys = []
    yr = []
    yrn = []
    #tr = random.randint(e, h)
    tr = 120
    prog_bar = 0
    bar = pbar(max_value=9)

    plt.figure(figsize=(15,7))
    ax = plt.axes()
    for u in np.arange (0.1, 1, 0.1):
        u = round(u, 1)
        sched_steady = []
        sched_reboot = []
        sched_reboot_normal = []
        for _ in range(50000):
            c, t, factors = task_generator(n, u, h, e, tr)
            sched_reboot.append(schedulability(n, c, t, u, h, tr, e+over))
            sched_reboot_normal.append(schedulability(n, c, t, u, h, tr, e))
            sched_steady.append(schedulability(n, c, t, u, h, 0, e))
        prog_bar += 1
        bar.update(prog_bar)
        yr.append(sched_reboot)
        yrn.append(sched_reboot_normal)
        ys.append(sched_steady)

        x.append(u)

    #with open('exp9.csv', 'w') as fn:
    #    writer = csv.writer(fn)
    #    writer.writerow(['Utilization', 'non-secboot sched', 'secboot sched'])
    #    for i in range(len(x)):
    #        writer.writerow([x[i], ys[i], yr[i], yrn[i]])
    pos_yr = [round(i-0.15, 2) for i in 6*np.arange(0.1,1,0.1)]
    pos_yrn = [round(i, 2) for i in 6*np.arange(0.1,1,0.1)]
    pos_ys = [round(i+0.15, 2) for i in 6*np.arange(0.1,1,0.1)]

    boxes = []
    colors = ['C0', 'C1', 'C2']
    boxes.append(ax.boxplot(yr, positions=pos_yr, whis=(0,100), widths=0.1,
                 patch_artist=True, whiskerprops=dict(color='C0')))
    boxes.append(plt.boxplot(yrn, positions=pos_yrn, whis=(0,100), widths= 0.1,
                 patch_artist=True, whiskerprops=dict(color='C1')))
    boxes.append(plt.boxplot(ys, positions=pos_ys, whis=(0,100), widths= 0.1,
                 patch_artist=True, whiskerprops=dict(color='C2')))

    ax.set_xlabel('System utilization', fontsize=fontsize+12)
    ax.set_ylabel('Percentage of schedulable tasks', fontsize=fontsize+10)
    legend_input = []

    for box, color in zip(boxes, colors):
        for b,w,m in zip(box['boxes'], box['whiskers'], box['medians']):
            b.set_color(color)
            m.set_color('black')
        legend_input.append(box['boxes'][0])


    ax.set_xticks(np.array(x)*6, x)
    ax.set_xlim(0, 6*1)
    ax.set_yticks([_*10 for _ in range(11)])
    ax.tick_params(axis='both', labelsize=fontsize+15)
    ax.set_ylim(0, 100)
    plt.legend(legend_input, ['SecureReboot', 'NormalReboot', 'NonReboot'],
               loc='upper center', ncol=3, bbox_to_anchor = (0,0.2,1,1), fontsize=fontsize+5)
    plt.rcParams.update({'font.size':25})
    plt.tight_layout()
    plt.savefig('BOX_AFPP_sched_n{}_h{}_tr{}.eps'.format(n,h,tr), format='eps')
    plt.show()

def experiment10():
    '''
    Experiment5 with Box and whisker plot
    Compares schedulability on 1000 random tasks for each utilization level
    fxed tr
    fixed e
    fixed h
    fixed n
    variable u
    '''
    e = 5.05
    over = 0.02856
    #e_ = 0.5*e
    n = 20
    h = 1000
    x = [0]
    ys = []
    yr = []
    yrn = []
    #tr = random.randint(e, h)
    tr = 120
    prog_bar = 0
    bar = pbar(max_value=9)

    plt.figure(figsize=(15,7))
    ax = plt.axes()
    for u in np.arange (0.1, 1, 0.1):
        u = round(u, 1)
        sched_steady = []
        sched_reboot = []
        sched_reboot_normal = []
        for _ in range(50000):
            c, t, factors = task_generator(n, u, h, e, tr)
            taskset = []
            for idx in range(len(c)):
                taskset.append((t[idx], c[idx]))

            c = []
            t = []
            for task in sorted(taskset):
                c.append(task[1])
                t.append(task[0])
            sched_reboot.append(schedulability(n, c, t, u, h, tr, e+over))
            sched_reboot_normal.append(schedulability(n, c, t, u, h, tr, e))
            sched_steady.append(schedulability(n, c, t, u, h, 0, e))
        prog_bar += 1
        bar.update(prog_bar)
        yr.append(sched_reboot)
        yrn.append(sched_reboot_normal)
        ys.append(sched_steady)

        x.append(u)

    #with open('exp9.csv', 'w') as fn:
    #    writer = csv.writer(fn)
    #    writer.writerow(['Utilization', 'non-secboot sched', 'secboot sched'])
    #    for i in range(len(x)):
    #        writer.writerow([x[i], ys[i], yr[i], yrn[i]])
    pos_yr = [round(i-0.15, 2) for i in 6*np.arange(0.1,1,0.1)]
    pos_yrn = [round(i, 2) for i in 6*np.arange(0.1,1,0.1)]
    pos_ys = [round(i+0.15, 2) for i in 6*np.arange(0.1,1,0.1)]

    boxes = []
    colors = ['C0', 'C1', 'C2']
    boxes.append(ax.boxplot(yr, positions=pos_yr, whis=(0,100), widths=0.1,
                 patch_artist=True, whiskerprops=dict(color='C0')))
    boxes.append(plt.boxplot(yrn, positions=pos_yrn, whis=(0,100), widths= 0.1,
                 patch_artist=True, whiskerprops=dict(color='C1')))
    boxes.append(plt.boxplot(ys, positions=pos_ys, whis=(0,100), widths= 0.1,
                 patch_artist=True, whiskerprops=dict(color='C2')))

    ax.set_xlabel('System utilization', fontsize=fontsize+15)
    ax.set_ylabel('Percentage of schedulable tasks', fontsize=fontsize+10)
    legend_input = []

    for box, color in zip(boxes, colors):
        for b,w,m in zip(box['boxes'], box['whiskers'], box['medians']):
            b.set_color(color)
            m.set_color('black')
        legend_input.append(box['boxes'][0])

    ax.set_xticks(np.array(x)*6, x)
    ax.set_xlim(0, 6*1)
    ax.set_yticks([_*10 for _ in range(11)])
    ax.tick_params(axis='both', labelsize=fontsize+15)
    ax.set_ylim(0, 100)
    plt.legend(legend_input, ['SecureReboot', 'NormalReboot', 'NonReboot'],
               loc='upper center', ncol=3, bbox_to_anchor = (0,0.2,1,1), fontsize=fontsize+5)
    plt.rcParams.update({'font.size':25})
    plt.tight_layout()
    #ax.set_ylim(0, 100)
    #plt.legend(legend_input, ['SecureReboot', 'NormalReboot', 'NonReboot'],
               #loc='upper center', ncol=3, bbox_to_anchor = (0,0.1,1,1))
    plt.savefig('BOX_RM_sched_n{}_h{}_tr{}.eps'.format(n,h,tr), format='eps')
    plt.show()

def experiment11():
    '''
    Variable tr 3D plot -- RM scheduling
    Compares schedulability on 1000 random tasks for each utilization level
    fixed e
    fixed h
    fixed n
    variable u
    '''
    e = 5
    e_ = 0.96*e
    n = 20
    h = 1000
    x = []
    zs = []
    zr = []
    zrn = []
    y = []
    prog_bar = 0
    bar = pbar(max_value=9*h)
    x = [round(i, 1) for i in np.arange(0,1,0.1)]

    for tr in range(1, 100):
        for u in np.arange (0.1, 1, 0.1):
            u = round(u, 1)
            sched_steady = []
            sched_reboot = []
            sched_reboot_normal = []
            for _ in range(10):
                c, t, factors = task_generator(n, u, h, e, tr)
               # taskset = []
               # for idx in range(len(c)):
               #     taskset.append((t[idx], c[idx]))

               # c = []
               # t = []
               # for task in sorted(taskset):
               #     c.append(task[1])
               #     t.append(task[0])
                sched_reboot.append(schedulability(n, c, t, u, h, tr, e))
                sched_reboot_normal.append(schedulability(n, c, t, u, h, tr, e_))
                sched_steady.append(schedulability(n, c, t, u, h, 0, e))
            prog_bar += 1
            bar.update(prog_bar)
            zr.append(stat.mean(sched_reboot))
            zrn.append(stat.mean(sched_reboot_normal))
            zs.append(stat.mean(sched_steady))
        y.append(tr)
    y.append(tr+1)


#    with open('exp8.csv', 'w') as fn:
#        writer = csv.writer(fn)
#        writer.writerow(['Utilization', 'non-secboot sched', 'secboot sched'])
#        for i in range(len(x)):
#            writer.writerow([x[i], ys[i], yr[i], yrn[i]])

#    x = np.array(x).reshape(9, h)
#    y = np.array(y).reshape(9, h)
#    zr = np.array(zr).reshape(9, h)
#    zrn = np.array(zrn).reshape(9, h)
#    zs = np.array(zs).reshape(9, h)
#    ax = plt.axes(projection='3d')
#    ax.plot_surface(x, y, zr, rstride=1, cstride=1,
#                cmap=plt.cm.YlGnBu_r, label='SecReboot', alpha=0.2)
#    ax.plot_surface(x, y, zs, rstride=1, cstride=1,
#                cmap='plasma', label='NonReboot', alpha=0.2)
    
    ax = plt.axes()
    x = np.array(x)
    y = np.array(y)
    z = np.array(zr)
    z = z.reshape(len(y)-1, len(x)-1)[::-1].transpose()
    print(z)

    im = ax.imshow(z, cmap='viridis', interpolation='nearest')

    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('Schedulability', rotation=-90, va='bottom',
                       rotation_mode='anchor')
    ax.set_xlabel('Utilization')
    ax.set_ylabel('Reboot Period (T_r)')
    plt.savefig('HeatMap_AFPP_var_tr_sched_n{}_h{}_tr{}.eps'.format(n,h,tr), format='eps')
    plt.show()

def weighted_sched():
    '''
    Compares schedulability on 1000 random tasks for each utilization level
    fxed tr
    fixed e
    fixed h
    fixed n
    variable u
    '''
    e = 5
    e_ = e
    n = 20
    h = 1000
    x = []
    ys = []
    yr = []
    yrn = []
    #tr = random.randint(e, h)
    #tr = 120
    prog_bar = 0
    #bar = pbar(max_value=9)
    wr = []
    wrn = []
    ws = []

    for tr in progress(range(h+1)):
        #e_ = e_iter*e/100
        ys = []
        yr = []
        yrn = []
        for u in np.arange (0.1, 1, 0.1):
            u = round(u, 1)
            sched_steady = []
            sched_reboot = []
            sched_reboot_normal = []
            for _ in range(1000):
                c, t, factors = task_generator(n, u, h, e, tr)
                sched_reboot.append(schedulability(n, c, t, u, h, tr, e))
                #sched_reboot_normal.append(schedulability(n, c, t, u, h, tr, e_))
                sched_steady.append(schedulability(n, c, t, u, h, 0, e))
            #bar.update(prog_bar)
            yr.append((stat.mean(sched_reboot)/100, u))
            #yrn.append((stat.mean(sched_reboot_normal)/100, u))
            ys.append((stat.mean(sched_steady)/100, u))
        prog_bar += 1
        #print(yr)
        wr.append(sum([i[0]*i[1] for i in yr])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]))
        #wrn.append(sum([i[0]*i[1] for i in yrn])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]))
        ws.append(sum([i[0]*i[1] for i in ys])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]))
    
        x.append(tr)

    with open('weighted.csv', 'w') as fn:
        writer = csv.writer(fn)
        writer.writerow(['Reboot Period', 'non-secboot sched', 'secboot sched'])
        for i in range(len(x)):
            writer.writerow([x[i], ws[i], wr[i]])

    plt.plot(x, wr, label='SecureReboot', fillstyle='none', markerfacecolor='none')
    #plt.plot(x, wrn, label='NormalReboot', fillstyle='none', markerfacecolor='none')
    plt.plot(x, ws,  label='NonReboot', fillstyle='none')
    plt.xlabel('Reboot Period')
    plt.ylabel('Weighted Schedulability')
    #plt.yscale('log')
    plt.xlim(0, 1000)
    plt.xticks([x*100 for x in range(11)])
    plt.yticks([round(i, 1) for i in np.arange(0.1,1.1,0.1)])
    #plt.xticks(np.arange(1, 101))
    plt.legend()
    plt.savefig('AFPP_weight_sched_var_tr_overhead_n{}_h{}_tr{}.eps'.format(n,h,tr), format='eps')
    plt.show()

def weighted_sched_rm():
    '''
    Compares weighted schedulability on 1000 random tasks for each utilization level RM
    fxed tr
    fixed e
    fixed h
    fixed n
    variable u
    '''
    e = 5
    e_ = e
    n = 20
    h = 1000
    x = []
    ys = []
    yr = []
    yrn = []
    #tr = random.randint(e, h)
    #tr = 120
    prog_bar = 0
    #bar = pbar(max_value=9)
    wr = []
    wrn = []
    ws = []

    for tr in progress(range(h+1)):
        #e_ = e_iter*e/100
        ys = []
        yr = []
        yrn = []
        for u in np.arange (0.1, 1, 0.1):
            u = round(u, 1)
            sched_steady = []
            sched_reboot = []
            sched_reboot_normal = []
            for _ in range(1000):
                c, t, factors = task_generator(n, u, h, e, tr)
                taskset = []
                for idx in range(len(c)):
                    taskset.append((t[idx], c[idx]))

                c = []
                t = []
                for task in sorted(taskset):
                    c.append(task[1])
                    t.append(task[0])
                sched_reboot.append(schedulability(n, c, t, u, h, tr, e))
                #sched_reboot_normal.append(schedulability(n, c, t, u, h, tr, e_))
                sched_steady.append(schedulability(n, c, t, u, h, 0, e))
            #bar.update(prog_bar)
            yr.append((stat.mean(sched_reboot)/100, u))
            #yrn.append((stat.mean(sched_reboot_normal)/100, u))
            ys.append((stat.mean(sched_steady)/100, u))
        prog_bar += 1
        #print(yr)
        wr.append(sum([i[0]*i[1] for i in yr])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]))
        #wrn.append(sum([i[0]*i[1] for i in yrn])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]))
        ws.append(sum([i[0]*i[1] for i in ys])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]))
    
        x.append(tr)

    with open('weighted_rm.csv', 'w') as fn:
        writer = csv.writer(fn)
        writer.writerow(['Reboot Period', 'non-secboot sched', 'secboot sched'])
        for i in range(len(x)):
            writer.writerow([x[i], ws[i], wr[i]])

    plt.plot(x, wr, label='SecureReboot', fillstyle='none', markerfacecolor='none')
    #plt.plot(x, wrn, label='NormalReboot', fillstyle='none', markerfacecolor='none')
    plt.plot(x, ws,  label='NonReboot', fillstyle='none')
    plt.xlabel('Reboot Period', fontsize=15)
    plt.ylabel('Weighted Schedulability', fontsize=15)
    #plt.yscale('log')
    plt.xlim(0, 1000)
    plt.xticks([x*100 for x in range(11)], fontsize=15)
    plt.yticks([round(i, 1) for i in np.arange(0.1,1.1,0.1)], fontsize=15)
    plt.rcParams.update({'font.size': 15}) #plt.xticks(np.arange(1, 101))
    plt.legend()
    plt.savefig('RM_weight_sched_var_tr_overhead_n{}_h{}_tr{}.eps'.format(n,h,tr), format='eps')
    plt.show()

def weighted_sched_var_e():
    '''
    Compares schedulability on 1000 random tasks for each utilization level
    fxed tr
    fixed e
    fixed h
    fixed n
    variable u
    '''
    #e = 5
    e_ = 5
    n = 20
    h = 1000
    x = []
    ys = []
    yr = []
    yrn = []
    #tr = random.randint(e, h)
    #tr = 120
    prog_bar = 0
    #bar = pbar(max_value=9)
    wr = []
    wrn = []
    ws = []

    for e_iter in progress(range(0, 101)):
        tempr = []
        temprn = []
        e = e_*(1+e_iter/100)
        for tr in range(h+1):
            #e_ = e_iter*e/100
            ys = []
            yr = []
            yrn = []
            for u in np.arange (0.1, 1, 0.1):
                u = round(u, 1)
                sched_steady = []
                sched_reboot = []
                sched_reboot_normal = []
                for _ in range(10):
                    c, t, factors = task_generator(n, u, h, e, tr)
                    sched_reboot.append(schedulability(n, c, t, u, h, tr, e))
                    sched_reboot_normal.append(schedulability(n, c, t, u, h, tr, e_))
                    #sched_steady.append(schedulability(n, c, t, u, h, 0, e))
                #bar.update(prog_bar)
                yr.append((stat.mean(sched_reboot)/100, u))
                yrn.append((stat.mean(sched_reboot_normal)/100, u))
                #ys.append((stat.mean(sched_steady)/100, u))
            prog_bar += 1
            #print(yr)
            tempr.append((sum([i[0]*i[1] for i in yr])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]), tr))
            temprn.append((sum([i[0]*i[1] for i in yrn])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]), tr))
            #ws.append(sum([i[0]*i[1] for i in ys])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]))
        wr.append(sum([i[0]*i[1] for i in tempr])/sum([i[1] for i in tempr]))
        wrn.append(sum([i[0]*i[1] for i in temprn])/sum([i[1] for i in temprn]))
        
        x.append(e_iter/100)

    with open('weighted_var_e.csv', 'w') as fn:
        writer = csv.writer(fn)
        writer.writerow(['Reboot Period', 'normal reboot sched', 'secboot sched'])
        for i in range(len(x)):
            writer.writerow([x[i], wrn[i], wr[i]])

    plt.plot(x, wr, label='SecureReboot', fillstyle='none', markerfacecolor='none')
    plt.plot(x, wrn, label='NormalReboot', fillstyle='none', markerfacecolor='none')
    #plt.plot(x, ws,  label='NonReboot', fillstyle='none')
    plt.xlabel('Secure Reboot overhead fraction')
    plt.ylabel('Weighted Schedulability')
    plt.yscale('log')
    plt.xlim(0, 101)
    plt.xticks([i/100 for i in range(101)])
    plt.yticks([round(i, 1) for i in np.arange(0.1,1.1,0.1)])
    #plt.xticks(np.arange(1, 101))
    plt.legend()
    plt.savefig('AFPP_weight_sched_var_e_overhead_n{}_h{}_tr{}.eps'.format(n,h,tr), format='eps')
    plt.show()

def weighted_sched_var_e_rm():
    '''
    Compares schedulability on 1000 random tasks for each utilization level
    fxed tr
    fixed e
    fixed h
    fixed n
    variable u
    '''
    #e = 5
    e_ = 5
    n = 20
    h = 1000
    x = []
    ys = []
    yr = []
    yrn = []
    #tr = random.randint(e, h)
    #tr = 120
    prog_bar = 0
    #bar = pbar(max_value=9)
    wr = []
    wrn = []
    ws = []

    for e_iter in progress(range(0, 101)):
        tempr = []
        temprn = []
        e = e_*(1+e_iter/100)
        for tr in range(h+1):
            #e_ = e_iter*e/100
            ys = []
            yr = []
            yrn = []
            for u in np.arange (0.1, 1, 0.1):
                u = round(u, 1)
                sched_steady = []
                sched_reboot = []
                sched_reboot_normal = []
                for _ in range(10):
                    c, t, factors = task_generator(n, u, h, e, tr)
                    taskset = []
                    for idx in range(len(c)):
                        taskset.append((t[idx], c[idx]))

                    c = []
                    t = []
                    for task in sorted(taskset):
                        c.append(task[1])
                        t.append(task[0])
                    sched_reboot.append(schedulability(n, c, t, u, h, tr, e))
                    sched_reboot_normal.append(schedulability(n, c, t, u, h, tr, e_))
                    #sched_steady.append(schedulability(n, c, t, u, h, 0, e))
                #bar.update(prog_bar)
                yr.append((stat.mean(sched_reboot)/100, u))
                yrn.append((stat.mean(sched_reboot_normal)/100, u))
                #ys.append((stat.mean(sched_steady)/100, u))
            prog_bar += 1
            #print(yr)
            tempr.append((sum([i[0]*i[1] for i in yr])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]), tr))
            temprn.append((sum([i[0]*i[1] for i in yrn])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]), tr))
            #ws.append(sum([i[0]*i[1] for i in ys])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]))
        wr.append(sum([i[0]*i[1] for i in tempr])/sum([i[1] for i in tempr]))
        wrn.append(sum([i[0]*i[1] for i in temprn])/sum([i[1] for i in temprn]))
        
        x.append(e_iter/100)

    with open('weighted_var_e_rm.csv', 'w') as fn:
        writer = csv.writer(fn)
        writer.writerow(['Reboot Period', 'normal reboot sched', 'secboot sched'])
        for i in range(len(x)):
            writer.writerow([x[i], wrn[i], wr[i]])

    plt.plot(x, wr, label='SecureReboot', fillstyle='none', markerfacecolor='none')
    plt.plot(x, wrn, label='NormalReboot', fillstyle='none', markerfacecolor='none')
    #plt.plot(x, ws,  label='NonReboot', fillstyle='none')
    plt.xlabel('Secure Reboot overhead fraction')
    plt.ylabel('Weighted Schedulability')
    plt.yscale('log')
    plt.xlim(0, 101)
    plt.xticks([i/100 for i in range(101)])
    plt.yticks([round(i, 1) for i in np.arange(0.1,1.1,0.1)])
    #plt.xticks(np.arange(1, 101))
    plt.legend()
    plt.savefig('RM_weight_sched_var_e_overhead_n{}_h{}_tr{}.eps'.format(n,h,tr), format='eps')
    plt.show()

def weighted_sched_box():

    e = 5
    e_ = e
    n = 20
    h = 1000
    x = []
    ys = []
    yr = []
    yrn = []
    #tr = random.randint(e, h)
    #tr = 120
    prog_bar = 0
    #bar = pbar(max_value=9)
    wr = []
    wrn = []
    ws = []

    for tr in progress(range(h+1)):
        #e_ = e_iter*e/100
        ys = []
        yr = []
        yrn = []
        for u in np.arange (0.1, 1, 0.1):
            u = round(u, 1)
            sched_steady = []
            sched_reboot = []
            sched_reboot_normal = []
            for _ in range(1000):
                c, t, factors = task_generator(n, u, h, e, tr)
                sched_reboot.append((schedulability(n, c, t, u, h, tr, e)/100, u))
                #sched_reboot_normal.append(schedulability(n, c, t, u, h, tr, e_))
                sched_steady.append((schedulability(n, c, t, u, h, 0, e)/100, u))
            #bar.update(prog_bar)
            #yr.append((stat.mean(sched_reboot)/100, u))
            #yrn.append((stat.mean(sched_reboot_normal)/100, u))
            #ys.append((stat.mean(sched_steady)/100, u))
        yr = sched_reboot.copy()
        ys = sched_reboot.copy()
        prog_bar += 1
        #print(yr)
        wr.append(sum([i[0]*i[1] for i in yr])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]))
        #wrn.append(sum([i[0]*i[1] for i in yrn])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]))
        ws.append(sum([i[0]*i[1] for i in ys])/sum([round(i,1) for i in np.arange(0.1, 1, 0.1)]))
    
        x.append(tr)

    with open('weighted_box.csv', 'w') as fn:
        writer = csv.writer(fn)
        writer.writerow(['Reboot Period', 'non-secboot sched', 'secboot sched'])
        for i in range(len(x)*1000):
            writer.writerow([x[i], ws[i], wr[i]])

    plt.plot(x, wr, label='SecureReboot', fillstyle='none', markerfacecolor='none')
    #plt.plot(x, wrn, label='NormalReboot', fillstyle='none', markerfacecolor='none')
    plt.plot(x, ws,  label='NonReboot', fillstyle='none')
    plt.xlabel('Reboot Period')
    plt.ylabel('Weighted Schedulability')
    #plt.yscale('log')
    plt.xlim(0, 1000)
    plt.xticks([x*100 for x in range(11)])
    plt.yticks([round(i, 1) for i in np.arange(0.1,1.1,0.1)])
    #plt.xticks(np.arange(1, 101))
    plt.legend()
    plt.savefig('AFPP_weight_sched_var_tr_box_n{}_h{}_tr{}.eps'.format(n,h,tr), format='eps')
    plt.show()

def run():
    #experiment1()
    #experiment2()
    #experiment3()
    ##experiment4()
    #experiment5()
    #experiment6()
    #experiment7()
    #experiment8()
    #experiment9()
    experiment10()
    #experiment11()
    #weighted_sched()
    #weighted_sched_rm()
    #weighted_sched_var_e()
    #weighted_sched_var_e_rm()
    #weighted_sched_box()

if __name__ == '__main__':
    #tasks = task_gen_handler(n, 1000, 1000, 5, 10)
    run()
