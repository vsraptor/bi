import numpy as np
import math
import warnings
from encoder import Encoder
from bmap1D import BMap1D
import logging as log

class ScalarEncoder(Encoder):

	def __init__(self, minimum=0,maximum=100,buckets=100,width=5,nbits=None):
		self.vmin = minimum
		self.vmax = maximum
		self.vrange = self.vmax - self.vmin
		self.width = width
		self.ext = 'se'
		if (nbits is None) :
			self.buckets = buckets
			self.nbits = buckets + width #+ 1
		else :
			self.nbits = nbits
			self.buckets = nbits - width #+ 1

		#what range of values, single bucket covers
		self.resolution = self.vrange/float(self.buckets)

		self.buffer = None #net buffer

		log.debug('> Scalar encoder: min:%s, max:%s, w:%s, buckets:%s, nb:%s' % (self.vmin,self.vmax,self.width,self.buckets,self.nbits))

	@property
	def info(self):
		s = "> Scalar encoder -----\n"
		s += "min-max/range : %s-%s/%s\n" % (self.vmin,self.vmax,self.vrange)
		s += "buckets,width,n : %s,%s,%s\n" % (self.buckets,self.width,self.nbits)
		s += "resolution : %.2f, %.4f%%\n" % (self.resolution, self.resolution/float(self.vrange))
		print s

	def pos(self, value) :
#		if value == 0 : return 0
		return int( math.floor(self.buckets * ((value - self.vmin)/float(self.vrange)) ) )

	def np_encode(self, value):
		i = self.pos(value)
		rv = np.zeros(self.nbits,dtype='uint8')
		rv[i : i + self.width ] = 1
		return rv

	def np_decode(self, data):
		tmp = np.where(data == 1)[0]
		i = 0 if len(tmp) == 0 else tmp[0]
		value = ( (i * self.vrange) / float(self.buckets) ) + self.vmin
		return math.floor(value)

	#given the number of buckets make binary of the value
	def encode_bucket(self, value) :
		if value < self.vmin or value > self.vmax : warnings.warn("Value '%s' outside of range : [%s <=> %s]" % (value, self.vmin, self.vmax))
		#corner case for vmax
		i = self.buckets-1 if value == self.vmax else self.pos(value)
		rv = BMap1D(self.buckets)
		rv[i] = 1
		return rv

	#recieves binary of size(buckets) with 1, for the bucket number, returns value
	# if classify : we recv data-bin, not bucket-bit =so=> conv. to bucket-bin first and then decode
	def decode_bucket(self, data, classify=False) :
		if not classify : assert len(data) == self.buckets, "Wrong size of bucket-binary, expected(%s), got(%s)" % (self.buckets, len(data))

		tmp = data.one_idxs()
		i = 0 if len(tmp) == 0 else tmp[0]
		#map data-bin first-bit, to bucket-idx
		if classify : i = i * (self.buckets/float(self.nbits))

		#return midpoint value from the bucket-range
		return int( (self.resolution * i) + (self.resolution/2))


	def encode(self, value):
		if value < self.vmin or value > self.vmax : warnings.warn("Value '%s' outside of range : [%s <=> %s]" % (value, self.vmin, self.vmax))
		i = self.pos(value)
		rv = BMap1D(self.nbits)
		#rv.setall(0)
		end = i + self.width
		rv[i : end] = 1
		return rv

	def decode(self, data):
		tmp = data.one_idxs()
		i = 0 if len(tmp) == 0 else tmp[0]
		value = ( (i * self.vrange) / float(self.buckets) ) + self.vmin
		return math.floor(value)




#-----------------Networking capabilities-------------------------------------------------

	def net_recv(self,msg) : self.buffer = msg
	def net_send(self) :	return { "value" : self.encode(self.buffer) }
