import math

es = 20
ps = 40
em = 70 + 20
pm = 1000

r = []
r.append(em)

def rec():
    n = 0
    while(1):
        r.append(em + math.ceil((r[n]+45)/ps)*es)

        if (r[n+1] == r[n]):
            break
        n = n+1

    print(r)

def thrput():
    tr = 50
    ti = 40
    ri = 20

    f = [0,math.floor(tr/ti)
        + math.floor((tr - math.floor(tr/ti)*ti)/ri)]

    for n in range(2, 5):
        val = f[n-1] \
              + max(math.floor(n*tr/ti) - math.floor((n-1)*tr/ti) - 1, 0) \
              + (1 if (n*tr - math.floor(n*tr/ti)*ti) >= ri else 0) \
              + (1 if ri > ((n-1)*tr - math.floor((n-1)*tr/ti)*ti) else 0)

        print(((n-1)*tr - math.floor((n-1)*tr/ti)*ti))
        f.append(val)

    print(f)
                

thrput()
#rec()
