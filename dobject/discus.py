from cvxopt.base import matrix, spmatrix, spdiag
from cvxopt.solvers import qp, options
#options['show_progress'] = False
# These tolerances are in pixels.  There's not much point being better than
# 1 pixel in tolerance.
options['abstol'] = 0.5
options['reltol'] = 1e-6
options['feastol'] = 0.5
options['maxiters'] = 250
from math import sqrt

# a = list of ideal x positions
# b = list of ideal y positions
# r = list of radii
# bounds = (lower x, upper x, lower y, upper y)
def findpos(a, b, r, bounds=None, float_r=True):
    alpha = 10.0 # preference for moving circles over shrinking them
    beta = 100 # Every circle would ideally be 100 pixels larger
    small = 0.01 # Initial radius for float_r
    # P and q represent the energy function, distance from (a,b), that we are
    # trying to minimize

    N = len(a)
    n = 2 * N

    pos = []
    pos.extend(a)
    pos.extend(b)
    if float_r:
        pos.extend(r)
    ideals = matrix(pos, tc='d')
    q = -ideals
    init = ideals
    if float_r:
        q[2*N:3*N] -= beta
        q[2*N:3*N] *= alpha
        init[2*N:3*N] = small

    if float_r:
        n = 3 * N
        
    ones = matrix(1, (1, n), tc='d')
    if float_r:
        ones[2*N:3*N] = alpha
    P = spdiag(ones)
    
    x = []
    I = []
    J = []
    hlist = []
    
    # x, I, and J, are the sparse coordinates for building G
    # G and h provide all the constraints
    # this loop adds the constraint that the projection of (the vector
    # between any two centers) onto (the vector connecting their ideal locations)
    # must not be shorter than the sum of their radii
    c = 0
    for i in range(N):
        for j in range(i+1, N):
            dx = a[i]-a[j]
            dy = b[i]-b[j]
            d = sqrt(dx*dx + dy*dy)
                        
            x.append(-dx)
            I.append(c)
            J.append(i)
            
            x.append(dx)
            I.append(c)
            J.append(j)
            
            x.append(-dy)
            I.append(c)
            J.append(i + N)
            
            x.append(dy)
            I.append(c)
            J.append(j + N)
            
            if float_r:
                x.append(d)
                I.append(c)
                J.append(i + 2*N)
            
                x.append(d)
                I.append(c)
                J.append(j + 2*N)
                
                hlist.append(0)
            else:
                hlist.append(-d*(r[i] + r[j]))
            
            c += 1
    
    if float_r:
        # Place upper and lower bounds on each radius
        for i in range(N):
            x.append(1)
            I.append(c)
            J.append(i + 2*N)
            hlist.append(r[i])
            
            c += 1
            
            x.append(-1)
            I.append(c)
            J.append(i + 2*N)
            hlist.append(0)
            
            c += 1

    if bounds is not None:
            lbx = bounds[0]
            ubx = bounds[1]
            lby = bounds[2]
            uby = bounds[3]
            for i in range(N):
                x.append(-1)
                I.append(c)
                J.append(i)
                
                x.append(1)
                I.append(c)
                J.append(i + 2*N)
                
                hlist.append(-lbx)
                c += 1

                x.append(1)
                I.append(c)
                J.append(i)
                
                x.append(1)
                I.append(c)
                J.append(i + 2*N)
                
                hlist.append(ubx)
                c += 1
                
                x.append(-1)
                I.append(c)
                J.append(i + N)
                
                x.append(1)
                I.append(c)
                J.append(i + 2*N)
                
                hlist.append(-lby)
                c += 1

                x.append(1)
                I.append(c)
                J.append(i + N)
                
                x.append(1)
                I.append(c)
                J.append(i + 2*N)
                
                hlist.append(uby)
                c += 1
    
    else:
        if bounds is not None:
            lbx = bounds[0]
            ubx = bounds[1]
            lby = bounds[2]
            uby = bounds[3]
            for i in range(N):
                x.append(-1)
                I.append(c)
                J.append(i)
                hlist.append(-r[i]-lbx)
                c += 1

                x.append(1)
                I.append(c)
                J.append(i)
                hlist.append(ubx-r[i])
                c += 1
                
                x.append(-1)
                I.append(c)
                J.append(i + N)
                hlist.append(-r[i]-lby)
                c += 1

                x.append(1)
                I.append(c)
                J.append(i + N)
                hlist.append(uby-r[i])
                c += 1
    
    G = spmatrix(x, I, J)
    h = matrix(hlist, tc='d')
    
    #this line actually solves the problem
    initvals = {}
    initvals['x'] = init
    #print init
    if float_r:
        initvals['s'] = h - G*init
        #print initvals['s']
    initvals['y'] = matrix(1, (0,1), tc='d')
    # z is actually supposed to satisfy Px + G*s + Ay + c = 0, so this definition
    # is extremely far from correct
    #initvals['z'] = 0 * h 
    
    outdict = qp(P, q, G, h, initvals=initvals)
    #print outdict
    if outdict['status'] == 'optimal':    
        bestpos = outdict['x']
        #print bestpos - ideals
        
        bestx = bestpos[:N]
        besty = bestpos[N:2*N]
        if float_r:
            bestr = bestpos[2*N:3*N]
        else:
            bestr = r
    
        return (list(bestx), list(besty), list(bestr))
    else:
        return None
