#!/usr/bin/env python
import re
import logging as log
import datetime as dt

import os, sys
basedir = os.path.abspath(os.path.dirname(__file__))
libdir = os.path.abspath(os.path.join(basedir, '../lib'));
sys.path.append(libdir)


from kdb import *
from bi_light import *
from bi_engine import *

log.root.setLevel(log.INFO)

results = []
kdb = KDB(items=100)

@bilight(kdb)
def star_wars():

	+ female(leia)
	+ male(luke)
	+ male(vader)
	+ male(kylo)
	+ female(padme)
	+ male(han)
	+ male(ruwee)
	+ female(jobal)
	+ female(shmi)

	+ child(luke, vader)
	+ child(leia, vader)
	+ child(leia, padme)
	+ child(kylo, leia)
	+ child(kylo, han)
	+ child(luke, padme)
	+ child(padme, ruwee)
	+ child(padme, jobal)
	+ child(vader, shmi)

	son(X,Y) << ( child(X,Y), male(X) )
	daughter(X,Y) << ( female(X), child(X,Y) )
	ds(X,Y) << ( daughter(X,Y) )
	ds(X,Y) << ( son(X,Y) )

	grandchild(X,Z) << ( child(X,Y), child(Y,Z) )
	gc_ds(X,Z) << ( ds(X,Y), ds(Y,Z) )
	gcm(X,Y) << ( grandchild(X,Y), male(X) )
	rgcm(X,Y) << ( male(X), grandchild(X,Y) )
	bgcm(X,Y) << ( male(X), grandchild(X,Y), male(X) )


def test(eng, fun, terms, res=None) :
	ts = dt.datetime.now()
	rv = eng.run(fun, terms)
	te = dt.datetime.now()
	time_taken = te - ts

	query = fun + str(terms)
	results.append([rv == res, query , rv,  str(time_taken)])


e = BiEngine(kdb)

tests = [
	[ 'male', ['han'], {} ],
	[ 'female', ['shmi'], {} ],
	[ 'child', ['X', 'ruwee'], {'X' : 'padme' } ],
	[ 'child', ['padme', 'X'], { 'X' : 'ruwee' } ],
	[ 'male', ['X'], {'X' : 'luke'} ],
	[ 'female', ['X'], {'X' : 'leia'} ],
	[ 'child', ['X','Y'], {'Y' : 'vader', 'X' : 'luke'} ],
	[ 'son', ['X','Y'], {'X' : 'luke', 'Y' : 'vader'} ],
	[ 'son', ['X','padme'], {'X' : 'luke'} ],
	[ 'daughter', ['X','Y'], {'X' : 'leia', 'Y' : 'vader'} ],
	[ 'daughter', ['padme','X'], {'X' : 'ruwee'} ],
	[ 'grandchild', ['X','Y'], {'X' : 'luke', 'Y' : 'shmi'} ],
	[ 'grandchild', ['X','vader'], {'X' : 'kylo'} ],
	[ 'grandchild', ['leia','X'], {'X' : 'shmi'} ],
	[ 'grandchild', ['leia','shmi'], {} ],
	[ 'gcm', ['X','vader'], {'X' : 'kylo'} ],
	[ 'gcm', ['luke','X'], {'X' : 'shmi'} ],
	[ 'rgcm', ['X','vader'], {'X' : 'kylo'} ],
	[ 'bgcm', ['X','vader'], {'X' : 'kylo'} ],

]


for x in tests :
	test(e, x[0], x[1], x[2] )

print "\n\n======================================================\n"
for r in results :
	print r



