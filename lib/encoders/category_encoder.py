import numpy as np
import math
from encoder import Encoder
from bmap1D import *

class CategoryEncoder(Encoder) :

	def __init__(self, nbits, ncats):
		self.ncats = ncats
		self.nbits = nbits
		self.width = nbits / ncats
		assert self.nbits % self.ncats == 0, "Categories cannot overlap"

	@property
	def info(self):
		s = "> Category encoder -----\n"
		s += "Num of categories : %s\n" % self.ncats
		s += "Num of bits : %s\n" % self.nbits
		print s

	def encode(self, value):
		i = int( math.floor((value-1) * self.width) )
		assert i < self.nbits or value < 0, "category value outside of range"
		rv = BMap1D(self.nbits)
		rv[i : i + self.width ] = 1
		return rv

	def decode(self, data):
		tmp = data.one_idxs()
		i = 0 if len(tmp) == 0 else tmp[0]
		value = int( math.floor( i / self.width ))
		return value+1

	def np_encode(self, value):
		i = int( math.floor((value-1) * self.width))
		assert i < self.nbits or value < 0, "category value outside of range"
		rv = np.zeros(self.nbits, dtype='uint8')
		rv[i : i + self.width ] = 1
		return rv

	def np_decode(self, data):
		tmp = np.where(data == 1)[0]
		i = 0 if len(tmp) == 0 else tmp[0]
		value = math.floor( i / self.width )
		return value+1

