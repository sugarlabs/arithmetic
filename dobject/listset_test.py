from dobject.groupthink.listset import *
from random import random

class SquareCompare:
    XSIZE = 24
    YSIZE = 18
    NUMBOXES = 1000
    def __init__(self,xsize = XSIZE, ysize = YSIZE,
                 numboxes = NUMBOXES):
        self.numboxes = numboxes
        self._boxes = [((xsize-1)*random(), (ysize-1)*random())
                                                     for i in range(numboxes)]
    
    def compute_overlaps_simple(self):
        overlaps = dict()
        for i in range(self.numboxes):
            for j in range(i+1, self.numboxes):
                d = self.distance(i,j)
                if d[0] != 0 and d[1] != 0:
                    overlaps[(i,j)] = d
        return overlaps
    
    def distance(self, i, j):
        return (max(0, 1-abs(self._boxes[i][0] - self._boxes[j][0])),
                max(0, 1-abs(self._boxes[i][1] - self._boxes[j][1])))
    
    def force(self, i, j):
        xi = self._boxes[i][0]
        yi = self._boxes[i][1]
        xj = self._boxes[j][0]
        yj = self._boxes[j][1]
        dist_x = min(xi + 1 - xj, xj + 1 - xi)
        dist_y = min(yi + 1 - yj, yj + 1 - yi)
        if dist_x > 0 and dist_y > 0:
            fx = cmp(4*xi + 3, 4*xj + 2)*dist_y
            fy = cmp(4*yi + 1, 4*yj + 2)*dist_x
            return (fx, fy)
        else:
            return (0, 0)
    
    def compute_overlaps_complex(self):
        overlaps = dict()
        fancy = Overlap2D()
        for i in range(self.numboxes):
            box = self._boxes[i]
            x1 = box[0]
            x2 = x1 + 1
            y1 = box[1]
            y2 = y1 + 1
            fancy.add(i, x1, x2, y1, y2)
            for j in fancy.overlaps(x1, x2, y1, y2):
                if j != i:
                    d = self.distance(i,j)
                    overlaps[(j,i)] = d
        return overlaps

"""
from time import time
for n in xrange(10, 2000, 10):
    c = SquareCompare(numboxes=n)
    t0 = time()
    o1 = c.compute_overlaps_complex()
    t1 = time() - t0
    t0 = time()
    o2 = c.compute_overlaps_simple()
    t2 = time() - t0
    print("n=" + str(n) + " Complex: " + str(t1) + " Simple: " + str(t2) + 
    " Valid: " + str(o1 == o2))
"""

import cProfile
import pstats
c = SquareCompare(numboxes=20)
cProfile.run('for i in xrange(1000): c.compute_overlaps_complex()','prof20.txt')
s = pstats.Stats('prof20.txt')
s.sort_stats('time')
s.print_stats()

