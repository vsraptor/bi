import numpy as np
import math
from bmap1D import *
from encoder import Encoder

def cumsum(lst):
	total = 0; rv = []
	for el in lst :
		total += el
		rv.append(total)
	return rv

class UnevenCategoryEncoder(Encoder) :

	#bluprint is list of pairs : (cat_num,nbits)
	def __init__(self, blueprint):
		assert isinstance(blueprint, list), "expecting list of pairs (cat_num, nbits)"
		self.ncats = len(blueprint)
		self.blueprint = blueprint
		#sum the bits to get total len
		self.nbits = reduce(lambda a,b : (0, a[1] + b[1]), self.blueprint)[1]
		self.cats = map(lambda a: a[0], self.blueprint)
		self.pos = [0] + cumsum(map(lambda a: a[1], self.blueprint))

		self.info()

	def info(self):
		print "> Uneven Category encoder -----"
		print "Num of categories : %s" % self.ncats
		print "Num of bits : %s" % self.nbits
		print "Blueprint : %s" % self.blueprint

	def encode(self, value):
		assert value in self.cats, "Value does not match any category : %s" % value
#		rv = np.zeros(self.nbits, dtype='uint8')
		rv = BMap1D(self.nbits)
		pos = 0
		for cat, nbits in self.blueprint :
			if value == cat : rv[ pos : pos + nbits ] = 1
			pos += nbits
		return rv

	def decode(self, sdr):
		tmp = sdr.one_idxs() + 1
		i = 0 if len(tmp) == 0 else tmp[0]
		res = -1
		for idx, pos in enumerate(self.pos) :#find the index
			if i > pos : res = idx
			else: break

		if res == -1 : warnings.warn("UCE: not a valid category")
		return self.cats[res]
