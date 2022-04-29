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
    if tr > 0:
        sumU = max(U - float(e/tr), 0)
    else:
        sumU = U
        print(sumU)
    for i in range(0, n):
        nextsumU = sumU*np.random.uniform(1/(n-i))
        vec.append(sumU - nextsumU)
        sumU = nextsumU
    vec[n-1] = sumU

    return vec

def throughput(t, tr, ri_se, ri_re, i, h):

    if tr > 0:
        f  = [1 if (ri_re <= tr and ri_re <= t[i]) else 0]

        for n in range(1, int(h/t[i])):
            f.append(f[n-1] + (1 if (math.ceil(n*t[i]/tr)*tr - n*t[i]) >= ri_re and \
                                     (n+1)*t[i] - n*t[i] >= ri_re else 0))
    else:
        if t[i] >= ri_se:
            f = [h/t[i]]
        else:
            f = [0]

    return f[-1]/h

def task_generator(n, u, h, e, tr):
    tasks = UUniFast(n, u, e, tr)
    t = []
    c = []
    factors = [i for i in range(1, h+1) if h%i == 0]

    for task in tasks:
        if task > 0:
            p = random.choice(factors)
        else:
            p = 0
        t.append(p)
        c.append(task*p)

    return (c, t, factors)

def run():
    e = 5
    i = 99
    h_vec = []
    n = 100
    h = 1000

    x = []
    thrpt1 = []
    thrpt2 = []
    u_vec = []

    u = 0.5
    

    for tr in range(e, h):
        c, t, tr_vec = task_generator(n, u, h, e, tr) 
        ri_re = reboot_ri(c,t,i,e)
        ri_se = steady_ri(c,t,i)
        alpha = 0
        beta = 0
        
        if t[i] > 0:
            alpha = throughput(t, tr, ri_se, ri_re, i, h)
            beta = throughput(t, 0, ri_se, ri_re, i, h)
            thrpt1.append(alpha)
            thrpt2.append(beta)
            x.append(tr)
            u_vec.append(u)

        if alpha > beta or alpha == 0:
            print(t[i], c[i], ri_se, ri_re, h, tr)



        

    plt.plot(x, thrpt1, label = 'SecBoot')
    plt.plot(x, thrpt2, label = 'non-SecBoot')

    plt.xlabel('$T_r $')
    plt.ylabel('$Throughput $')
    #plt.xscale('log')

    plt.legend()

    plt.show()

run()
