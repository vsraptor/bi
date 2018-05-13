import numpy as np
import math
from encoder import Encoder
from bmap1D import BMap1D
from category_encoder import *

class MonthEncoder(Encoder):

	months = {
		'january' : 1, 'jan' : 1,
		'february' : 2, 'feb' : 2,
		'march' : 3, 'mar' : 3,
		'april' : 4, 'apr' : 4,
		'may' : 5,
		'june' : 6, 'jun' : 6,
		'july' : 7, 'jul' : 7,
		'august' : 8, 'aug' : 8,
		'september' : 9, 'sep' : 9,
		'october' : 10, 'oct' : 10,
		'november' : 11, 'nov' : 11,
		'december' : 12, 'dec' : 12
	}
	months_inv = dict((v, k) for k, v in months.iteritems())

	def __init__(self, nbits=24):
		assert nbits % 12 == 0, "Number of bits used for MONTH, should be divisible be 12"
		self.ce = CategoryEncoder(nbits=nbits,ncats=12)

	@property
	def info(self):
		s = "> Month encoder -----\n"
		s += "width,n : %s,%s\n" % (self.ce.width,self.ce.nbits)
		print s

	def encode(self, value) :
		value = MonthEncoder.months[value.lower()] if isinstance(value,basestring) else value
		return self.ce.encode(value-1)

	def decode(self, value, as_str=False) :
		res = int(self.ce.decode(value)) + 1
		if as_str : return MonthEncoder.months_inv[res]
		return res

