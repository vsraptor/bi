from bmap2D import *
from bitarray import bitarray

"""

	Universal hashing : uses random matrix of 0|1.

		count = (matrix & input_value).count()
		parity_bin = count % 2
		convert the binary to integer

"""

class MxHash:

	def __init__(self, max_in=4096, max_out=2048, randomize=0.5):
		self.max_in = max_in
		self.max_out = max_out
		ibits = np.log2(self.max_in)
		obits = np.log2(self.max_out)
		self.ibits = int(np.ceil(ibits))
		self.obits = int(np.ceil(obits))

		assert ibits % self.ibits == 0, "max input value has to be exact power of 2"
		assert obits % self.obits == 0, "max output value has to be exact power of 2"

		self.mx = BMap2D(self.obits, self.ibits, randomize=randomize)

	def hashit(self, value):
		assert 0 <= value <= self.max_in

		#make zero padded binary string from int
		bstr = bin(value)[2:].zfill(self.ibits)
		dup = self.mx.repeat( bitarray(bstr) )
		olap = self.mx & dup

		#count 1s parity i.e. odd=1, even=0
		cnt = olap.count_ones(axis='rows') % 2

		#convert 0|1 numpy array to integer
		rv = cnt.dot( 1 << np.arange(cnt.size)[::-1] )
		#print "rv> %s" % rv

		#print "cnt> %s" % cnt
		#ba = bitarray()
	 	#ba.pack(cnt.astype(np.bool).tostring())
		#convert from bitarray 0|1 to integer
		#return int( ba.to01(), 2 )
		return rv




