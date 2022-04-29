#!/usr/bin/env python

import math

def steady(c, t, i, e):
    r = [c[i]]
    n = 0

    while(1):
        i_hp = 0

        for j in range(i):
            i_hp += math.ceil((r[n])/t[j])*c[j]

        r.append(e + c[i] + i_hp)
        n = n+1

        print(r[n])
        if(r[n] == r[n-1] or r[n] > t[i]):
            break;
    return r[n]


c = [5,3,6]
t = [15, 20, 30]
i = 2

print(steady(c, t, i, 5))
