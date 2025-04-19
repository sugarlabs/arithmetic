import groupthink
x = groupthink.CausalTree()
t = groupthink.TubeBox()
h = groupthink.CausalHandler('qwer',t)
x.set_handler(h)

m = x.new_child(x.ROOT)
n = x.new_child(m)
o = x.new_child(n)
p = x.new_child(o)
q = x.new_child(p)

x.delete(n)
x.change_parent(p,x.ROOT)

print(m in x.get_children(x.ROOT))
print(p in x.get_children(x.ROOT))
print(x.get_parent(m) == x.get_parent(p) == x.ROOT)
print(q in x.get_children(p))
print(m == x.get_parent(o))
