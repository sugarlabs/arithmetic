import dobject.groupthink.stringtree as stringtree
import random
import io

x = stringtree.SimpleStringTree("base")
x.seek(2)
x.insert('ABC')
print(x.getvalue())
x.seek(5)
x.insert("123")
print(x.getvalue())
x.insert("#$%",4)
print(x.getvalue())
x.delete(5,4)
print(x.getvalue())
x.move(2,3,7)
print(x.getvalue())

def randstring(N=5):
    return "".join((random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890') for i in range(N)))

 
b = randstring(10)
x = stringtree.SimpleStringTree(b)
y = io.StringIO(b)
for i in range(100):
    #print(i)
    xs = x.getvalue()
    ys = y.getvalue()
    z = stringtree.SimpleStringTree()
    cs = x.get_changes()
    for c in cs:
        z.add_change(c)
    zs = z.getvalue()
    print((xs, x.tell()))
    print((ys, y.tell()))
    print(zs)
    if not (xs == ys == zs):
        raise
    n = random.randrange(0,len(xs)+1)
    s = randstring()
    #print(n, s)
    x.seek(n)
    y.seek(n)
    #print(x.tell(), y.tell())
    x.write(s)
    y.write(s)
    #print(x.tell(), y.tell())
    #print str(x)

# Linear performance test
z = stringtree.SimpleStringTree()
for i in range(10000):
    print(i)
    z.insert("a",i)
    z.delete(i,1)
    z.insert("b",i)
q = stringtree.SimpleStringTree()
cs = z.get_changes()
for c in cs:
    q.add_change(c)

