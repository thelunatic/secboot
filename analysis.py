#!/usr/bin/env python

import random
import math
import numpy as np
from matplotlib import pyplot as plt

cprio = 2
mprio = 1
sprio = 0

class task():
    def __init__(self, prio_level, prio, execution_time, period):
        self.prio_level = prio_level
        self.prio = prio
        self.e = execution_time
        self.p = period

def random_task_generator(n):
    c = []
    s = []
    m = [0]

    for i in range(n):
        t = task(sprio, i, random.randint(5, 10), random.randint(100, 200))
        s.append(t)
        t = task(cprio, i, random.randint(10, 20), random.randint(100, 1000))
        c.append(t)

    m[0] = task(mprio, 0, random.randint(10, 50), random.randint(10000, 15000))

    return (c, s, m)

def rc(t, comp, safety):
    e = t.e
    p = t.p
    r = []
    r.append(e)
    n = 0

    while(1):
        i = 0.000
        for s in safety:
            i += math.ceil(r[n]/s.p) * s.e

        for c in comp:
            if (c.prio<t.prio):
                i+= math.ceil(r[n]/c.p) * c.e

        r.append(e + i)
        if r[n+1] == r[n] or r[n] > t.p:
            break;
        n = n+1
    return r[n]

def run():
    c, s, m = random_task_generator(10)
    r = rc(c[-1], c, s)
    print("response: {}  deadline:{}".format(r, c[-1].p))
    if r > c[-1].p:
        print("Task not schedulable")
    else:
        print("Task Schedulable!!")

def UUniFast(n, U):
    vec = []
    sumU = U
    for i in range(1, n):
        nextsumU = sumU*np.random.uniform(1/(n-i))
        vec.append(sumU - nextsumU)
        sumU = nextsumU
    vec.append(sumU)

    print(len(vec))
    return(vec)

def plotthis():
    vec1 = UUniFast(1000, 1)
    vec2 = UUniFast(1000, 1)
    #vec3 = UUniFast(1000, 1)

    fig = plt.figure()
    ax = fig.add_subplot()#projection='3d')

    print(vec1)
    ax.scatter(vec1,
               vec2,)
               #vec3)

#    ax.set_xlim(0, 1)
#    ax.set_ylim(0, 1)
#    ax.set_zlim(0, 1)
    ax.set_xlabel('x U')
    #ax.set_ylabel('y U')
    #ax.set_zlabel('z U')
    plt.show()
    print(vec)
    
if __name__ == '__main__':
   # run()
   plotthis()
