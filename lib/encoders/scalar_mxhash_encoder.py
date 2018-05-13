from mx_hash import *
from bitarray import bitarray

class ScalarMxHash:

	def __init__(self, max_in, nbits=128, sparsity=0.02):
		assert np.log2(nbits) % int(np.log2(nbits)) == 0, "nbits must have value which equals power of two"
		self.max_in = max_in
		self.nbits = nbits
		self.sparsity = sparsity
		self.sparsity_bits = int(self.nbits * self.sparsity)
		self.avg_collision = 0
		self.collision_cnt = 0
		self.converted_cnt = 1
		#round up to the closeses power of 2
		self.power2_max_in = 2 ** int(np.ceil(np.log2( self.max_in )))
		self.mxhs = []
		for i in xrange(self.sparsity_bits):
			#number of bit is the max value for hashing function
			self.mxhs.append( MxHash(max_in=self.power2_max_in, max_out=self.nbits) )


	def encode(self, value):
		idxs = [ u.hashit(value) for u in self.mxhs ]
		rv = bitarray(self.nbits)
		rv.setall(0)
		for i in idxs : rv[i] = 1

		#calculate collision rate
		diff = self.sparsity_bits - int(rv.count())
		#print diff
		if diff > 0 : self.collision_cnt += 1
		self.avg_collision = (self.avg_collision + diff) / float(self.converted_cnt)
		self.converted_cnt += 1
		return rv

	def decode(self, sdr):
		return NotImplementedError