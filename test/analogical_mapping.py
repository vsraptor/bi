#!/usr/bin/env python
import re
import logging as log
import seaborn as sns

import imports
imports.import_lib()

from bi import *
from lexicon import *

"""

"""

class AMap :

	def __init__(self ):
		self.l = lex()
		self.l.az()
		self.r = [ #relations
			{ 'fun' : 'above', 'role1' : 'a1', 'role2' : 'a2' },
			{ 'fun' : 'below', 'role1' : 'b1', 'role2' : 'b2' },
		]
		self.l.add_items(['above','below', 'a1', 'a2', 'b1', 'b2'])
		self.train_data = [ ['a', 'b'], [ 'c', 'd' ], ['e','f'], ['g', 'h'], ['i','j'], ['k', 'l'], ['m','n'] ]
		self.test_data = [ ['x', 'y'], ['w', 'z' ], ['q','p'], ['a','b'], ['i','j'] ]


	def rel(self, filler1, filler2, rnum) :
		r1 = self.r[rnum]['role1'] 
		r2 = self.r[rnum]['role2']
		fun = self.r[rnum]['fun']
		print "relation: %s + %s * %s + %s * %s" % (fun,r1,filler1, r2, filler2)
		bind1 = self.l[r1] * self.l[filler1]
		bind2 = self.l[r2] * self.l[filler2]
		return sdp.bundle([ self.l[fun] , bind1, bind2 ])

	def mapx(self, fillers):
		r1 = self.rel(fillers[0], fillers[1],0)
		r2 = self.rel(fillers[1], fillers[0],1)
		return r1 * r2

	def train(self, tries=1):
		print ":----------- train ----------------"
		maps = []
		max_tries = len(self.train_data)
		if tries > max_tries : tries = max_tries
		for i in xrange(tries) :
			maps.append( self.mapx(self.train_data[i]) )
		if tries == 1 : return maps[0]
		return sdp.bundle(maps)

	def test(self, Map):
		print ":----------- test ----------------"
		for i in xrange(len(self.test_data)) :
			rel = self.rel(self.test_data[i][0], self.test_data[i][1], 0)
			rev = self.rel(self.test_data[i][1], self.test_data[i][0], 1)
			res = (Map * rel) % rev
			print "dist = (Map * relation) %% reverse : %s" % res

	def run(self) :
		Transform_Map = self.train(7)
		self.test(Transform_Map)



x = AMap()
x.run()

