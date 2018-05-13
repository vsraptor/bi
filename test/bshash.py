#!/usr/bin/env python
import re
import logging as log

import imports
imports.import_lib()

import string

"""
	This test test if BSHLex hashing works and how many bits it should be.
	The idea is to create a bundle of bind pairs and then try to extract the values (best match) correctly.

	The variables of the test are :
		- number of bind pairs : def 15
		- hbits : how many bits to sample to create hash : def 800
		- rand_items : how many random items to create in the lexer to mess with best-match process.
			The higher the number less probable that the hashing will be able to distinguish between items.

	The number of fail should be zero, for 100% correctness.

"""

from hashed_lex import *

stats = {}
s = { 'ok' : 0, 'fail' : 0, 'total' : 0 }
val = 'v'
#vals = [ 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'k' ]
vals = list(string.lowercase)

def test(bpairs, rand_items=500, hbits=768) :
	items = 20 + rand_items + len(vals) * bpairs
	print "> %s : items:%s, hbits:%s" % (bpairs, items, hbits)
	stats[rand_items] = s.copy()
	bsh = BSHLex(items=items, hbits_cnt=hbits)

	vnames = []
	for v in vals :
		for i in xrange(bpairs) :
			vnames.append( v+str(i) )

	syms = [ '$'+str(i) for i in xrange(bpairs) ]

	bsh.add_items(vnames)
	bsh.add_items(syms)
	bsh.rand_items(rand_items)

	for v in vals :
		b = []
		for i in xrange(bpairs) :
			bind = bsh['$'+str(i)] * bsh[v+str(i)]
			b.append(bind)

		bun = sdp.bundle(b)

		for i in xrange(bpairs) :
			correct = v + str(i)
			match = bsh.bm(bsh['$'+str(i)] * bun)
			if match == correct : stats[rand_items]['ok'] += 1
			else : stats[rand_items]['fail'] += 1
			stats[rand_items]['total'] += 1


for _ in xrange(5) :
	for r in xrange(0,500,100) :
		test(15, rand_items=r, hbits=1024)
		print stats[r]

#print "----------------------------"
#print stats
