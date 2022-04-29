#!/usr/bin/env python
import math
import random
import numpy as np
from matplotlib import pyplot as plt

def steady_ri(c, t, i):
    r = [c[i]]
    n = 0

    while(1):
        i_hp = 0

        for j in range(i):
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
            i_hp += math.ceil(r[n]/t[j])*c[j]

        r.append(e + c[i] + i_hp)
        n = n+1

        if(r[n] == r[n-1] or r[n] > t[i]):
            break;
    return r[n]

def RebootWindow(t, c, i, epsilon, tr):
    W = [0]
    r = steady(c, t, i)
    i1 = 0
    i2 = 0
    n = 0

    for j in range(i):
        i1 += math.floor(r/t[j])*c[j]
        i2 += min(r - math.floor(r/t[j])*t[j], c[j])

    interference = 2*c[i] + epsilon + i1 + i2
    W[0] += interference

    while(1):
        w_temp = 0

        for j in range(i):
            w_temp += math.ceil((W[n] - epsilon - r)/t[j])*c[j]

        W.append(interference + w_temp)
        n = n+1

        if (W[n] == W[n-1] or W[n] > tr):
            break;

    return W[n]

def UUniFast(n, U, e, tr):
    vec = []
    sumU = U - e/tr
    for i in range(0, n):
        nextsumU = sumU*np.random.uniform(1/(n-i))
        vec.append(sumU - nextsumU)
        sumU = nextsumU
    vec[n-1] = sumU

    return vec

def throughput(t, tr, ri, i, h):

    thruput =  0

    if (tr != 0):
        f = [0,math.floor(tr/t[i])
            + math.floor((tr - math.floor(tr/t[i])*t[i])/ri)]
        for n in range(2, int(h/tr)+1):
            val = f[n-1] \
                  + max(math.floor(n*tr/t[i]) - math.floor((n-1)*tr/t[i]) - 1, 0) \
                  + (1 if (n*tr - math.floor(n*tr/t[i])*t[i]) >= ri else 0) \
                  + (1 if (ri > ((n-1)*tr - math.floor((n-1)*tr/t[i])*t[i]) and \
                  ((math.ceil((n)*tr/t[i])*t[i]) - (n)*tr) > ri) else 0)

            f.append(val)
    
        thruput = f[-1]/h

    return thruput, 1/t[i]

def task_generator(n, u, h, e, tr):
    tasks = UUniFast(n, u, e, tr)
    t = []
    c = []
    factors = [i for i in range(1, h+1) if h%i == 0]

    for task in tasks:
        p = random.choice(factors)
        t.append(p)
        c.append(task*p)

    return (c, t, factors)
'''
def run():
    e = 5
    i = 4
    h_vec = []
    n = 500
    h = 5000

    x = []
    thrpt1 = []
    thrpt2 = []
    u_vec = []

    ax = plt.axes(projection = '3d')
    for u in range(1, 10):
        u = u/10
        c, t, tr_vec = task_generator(n, u, h) 
        ri = steady(c,t,i)

        for tr in [_ for _ in range(h) if h%_ == 0]:
    #        W = RebootWindow(t, c, n-1, e, tr)
            val_a, val_b = throughput(t, tr, ri, i, h)
            thrpt1.append(val_a)
            thrpt2.append(val_b)

            x.append(tr)
            u_vec.append(u)
    x1 = x.copy()
    x2 = x.copy()
    x, thrpt1 = np.meshgrid(x, thrpt1)
    x1, u_vec = np.meshgrid(x1, u_vec)
    x2, thrpt2 = np.meshgrid(x2, thrpt2)
    ax.plot_surface(np.array(x), np.array(u_vec), np.array(thrpt1), 
                    cstride=1, rstride=1,
                    label = 'SecBoot')
    ax.plot_surface(np.array(x), np.array(u_vec), np.array(thrpt2),
                    cstride=1, rstride=1,
                    label = 'non-SecBoot')

    ax.set_xlabel('Reboot period')
    ax.set_ylabel('Utilization')
    ax.set_zlabel('Throughput')

    #ax.legend()

    plt.show()
'''

def run1():
    e = 5
    i = 1
    h_vec = []
    n = 2
    h = 100

    x = []
    thrpt1 = []
    thrpt2 = []
    u_vec = []

    u = 0.8
    

    for tr in range(1, h):
        c, t, tr_vec = task_generator(n, u, h, e, tr) 
        ri = reboot_ri(c,t,i,e)
        alpha, beta = throughput(t, tr, ri, i, h)
        thrpt1.append(alpha)
        thrpt2.append(beta)

        if alpha > beta:
            print(t[i], c[i], ri, h, tr)

        x.append(tr)
        u_vec.append(u)


        

    plt.plot(x, thrpt1, label = 'SecBoot')
    plt.plot(x, thrpt2, label = 'non-SecBoot')

    plt.xlabel('$T_r $')
    plt.ylabel('$Throughput $')

    plt.legend()

    plt.show()

run1()
