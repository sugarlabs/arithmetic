from .discus import findpos
from random import randint

print(findpos([100, -100], [0,0], [500,400]))

print(findpos([200, 210], [100,100], [50,40], [0, 1200, 0, 800]))

print(findpos([200, 210], [100,100], [500,400], [0, 1200, 0, 800]))

a = []
b = []
r = []
W = 1200
H = 800
N = 50
for i in range(N):
    a.append(randint(1,W-1))
    b.append(randint(1,H-1))
    r.append(randint(200,250))

print(a, b, r)
print(findpos(a, b, r, [0, W, 0, H]))
