from kdb import *
from bi_light import *

kdb = KDB(items=100)

@bilight(kdb)
def abc():
	+ vv()
	+ vv(t1)
	+ vv(X, defs)
	+ vv(aaa, Y)
	p1(vv) << ( vv() )
	p1(vv,X) << ( vv(X), union(X,Y) )
	+ man(socrates)
	+ animal(donkey)
	human(X) << ( man(X) )
	+ atom()
	+ union(t1,t2)
	+ b(g1)
	+ b(g2)
	+ b(g3)
	bt(X) << (b(X), fail(X))
	+ fail(g3)

#	+ car([X|Y], X)
#	+ cdr([X|Y], Y)
#	+ cons(X,R,[X|R])





