import numpy as np
import math
from encoder import Encoder
from bmap1D import BMap1D
from scalar_encoder import *

class YearEncoder(Encoder):

	def __init__(self, nbits=100, yfrom=1950, yto=2050, width=5):
		self.yfrom = yfrom
		self.yto = yto
		self.se = ScalarEncoder(minimum=yfrom, maximum=yto, nbits=nbits, width=width)

	@property
	def info(self):
		s = "> Day encoder -----\n"
		s += "From : %s, to: %s\n" % (self.yfrom, self.yto)
		s += "buckets,width,n : %s,%s,%s\n" % (self.se.buckets,self.se.width,self.se.nbits)
		print s

	def encode(self, value) : return self.se.encode(value)
	def decode(self, value) : return int(self.se.decode(value))

