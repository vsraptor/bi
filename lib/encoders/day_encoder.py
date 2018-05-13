import numpy as np
import math
from encoder import Encoder
from bmap1D import BMap1D
from category_encoder import *

class DayEncoder(Encoder):

	def __init__(self, nbits=62):
		assert nbits % 31 == 0, "Number of bits used for DAY, should be divisible be 31"
		self.ce = CategoryEncoder(nbits=nbits,ncats=31)

	@property
	def info(self):
		s = "> Day encoder -----\n"
		s += "width,n : %s,%s\n" % (self.ce.width,self.ce.nbits)
		print s

	def encode(self, value) : return self.ce.encode(value)
	def decode(self, value) : return self.ce.decode(value)

