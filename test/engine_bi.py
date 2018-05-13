#!/usr/bin/env python
import re
import logging as log
import datetime as dt

import os, sys
basedir = os.path.abspath(os.path.dirname(__file__))
libdir = os.path.abspath(os.path.join(basedir, '../lib'));
libdir2 = os.path.abspath(os.path.join(basedir, '../lib/cups'));
sys.path.insert(0,libdir)


from kdb import *
from bi_engine import *
from bi_parser import *
from dyn_atoms import *

log.root.setLevel(log.INFO)


def test(eng, fun, terms, res=None) :
	ts = dt.datetime.now()
	rv = eng.query(fun, terms)
	te = dt.datetime.now()
	time_taken = te - ts

	query = fun + str(terms)
	results.append([rv == res, query , rv,  str(time_taken)])


results = []
kdb = KDB(items=100)
parser = BiParser(kdb=kdb,write2db=True)
parser.parse('./sw_bi_db.pl')
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



