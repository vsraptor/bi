import numpy as np
import math
from bmap1D import *
from encoder import Encoder

#Concatenate encoded results
class SpliceEncoders(Encoder):

	def __init__(self, encoders):
		self.encoders = encoders
		self.nbits = 0
		self.lens = []
		for enc in self.encoders :
			self.nbits += enc.nbits
			self.lens.append(self.nbits)

	@property
	def info(self):
		s = "=====================================\n"
		for e in self.encoders :
			e.info()
			s += "-----------------------------------\n"
		s += "Total number of bits : %s\n" % self.nbits
		print s

	#one data item per encoder
	def encode(self, data):
		assert len(data) == len(self.encoders), "Data <=> Encoder size mistmatch"
		bmap = BMap1D(self.nbits)
		for i, enc in enumerate(self.encoders) :
			b = enc.encode(data[i])
			#find start-end range of bits to change
			start = 0 if i == 0 else self.lens[i-1]
			bmap[ start : self.lens[i] ] = b
		return bmap


	def batch_encode(self, data):
		return NotImplementedError
		rv = np.zeros((len(data),self.nbits))
		for i in np.arange(len(data)) :
			rv[i] = self.encode(data[i])
		return rv


	def decode(self, sdr):
		assert len(sdr) == self.nbits, "Mismatch in the size of SDR (%s) expected %s" % (sdr.size, self.nbits)
		rv = []
		for i, enc in enumerate(self.encoders) :
			#find start-end range of bits to change
			start = 0 if i == 0 else self.lens[i-1]
			rv.append( enc.decode(sdr[start: self.lens[i]]) )
		return rv

	def batch_decode(self,data) :
		return NotImplementedError



