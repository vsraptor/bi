from bitarray import *
from bmap1D import *
from bmap2D import *
import numpy as np
from matplotlib import pyplot as plt

"""
	Convolution|XOR pair : The simplest possible compostion. Also Binded pair,
	Role : Left hand item from binded-pair
	Filler : Right hand item from binded-pair
	VV : Either one of the binded-pair. Shortcut from Variable-Value

"""


class sdp: #utility class

	ONE = bitarray("1")
	ZERO = bitarray("0")

	#how many times to try to generate truly random item
	random_trials = 0
	#Used for similarity matching, 
	#how many bits have to match for the result to be assumed TRUE
	true_thresh = 0.42 #yes this is that 42 ;)
	nbits = 10000

	@staticmethod
	def sdp2np(bits):
		return np.fromstring(bits.unpack(), dtype=np.bool).astype(np.int8)


	@staticmethod
	def null(nbits=nbits): return SDP(nbits)
	@staticmethod
	def full(nbits=nbits):
		rv = SDP(nbits)
		rv.setall(sdp.ONE)
		return rv

	@staticmethod
	def overlap(x, y): return int((x & y).count())
	@staticmethod #overlap sameness
	def same(x,y, opercent=0.9, sparsity=0.02):
		if sdp.overlap(x,y) > len(x) * sparsity * opercent : return True
		return False

	@staticmethod
	def bind(x,y=None):
		if y is not None : return x ^ y
		return sdp.bind_lst(x)
	@staticmethod
	def bind_lst(lst):
		if not isinstance(lst, list) or len(lst) < 2 : raise Exception("bind: Expecting a list with more than one element!")
		rv = lst[0]
		for el in lst[1:] : rv ^= el
		return rv

	@staticmethod
	def unbind(x,y): return x ^ y
	@staticmethod #given one returns the other from the pair or struct
	def probe(vv, struct): return vv ^ struct
	@staticmethod
	def mapit(x,y): return x ^ y
	@staticmethod
	def unmap(x,y): return x ^ y
	@staticmethod #hamming distance
	def dist(x,y) : return int(bitdiff(x,y)) #faster than : int((x ^ y).count())
	@staticmethod #normalized hamming distance
	def norm_dist(x,y) : return bitdiff(x,y) / float((x & y).count())
	@staticmethod
	def sim(x,y,thresh=true_thresh,nbits=nbits) : return ( bitdiff(x,y) / float(nbits) ) < thresh
	@staticmethod #check for pair in a structure
	def contain(pair, struct):
		hd = sdp.dist(pair,struct)
		if hd/float(len(struct)) < sdp.true_thresh : return True
		return False

	#Generate random permutation "pseudo-matrix", which you use in permute
	@staticmethod
	def rand_perm_mx(size=nbits):
		rv = np.arange(size)
		np.random.shuffle(rv)
		return rv
	pmx = rand_perm_mx #alias

	#mx is pseudo-matrix i.e. indicates which bits are swapped
	@staticmethod
	def permute(x,mx):
		rv = SDP(len(mx))
		for i, ix in enumerate(mx) : rv[ix] = x[i]
		return rv
	perm = permute

	@staticmethod
	def inv_permute(x,mx):
		rv = SDP(len(mx))
		for i, ix in enumerate(mx) : rv[i] = x[ix]
		return rv
	iperm = inv_permute

	@staticmethod #easy permutation
	def roll(x, steps):
		return x[-steps:].cat(x[:-steps])

	#non-comutative operations, "pmx" is permutation matrix.
	@staticmethod
	def permuted_bind(a, b, pmx):
		#if number use roll() instead of permute()
		if isinstance(pmx,int) : return sdp.bind(a, sdp.roll(b,pmx))
		return sdp.bind(a, sdp.permute(b,pmx))
	pbind = permuted_bind

	@staticmethod
	def permuted_probe(a, ab, pmx):
		#if number use roll() instead of permute()
		if isinstance(pmx,int) : return sdp.roll(sdp.bind(a, ab),-pmx)
		return sdp.inv_permute(sdp.bind(a, ab), pmx)
	pprobe = permuted_probe

	#Bundling, set composition, superposition, merge
	@staticmethod
	def bundle(lst, nbits=nbits):
		nrows = len(lst)
		vsum = np.zeros(nbits, dtype=np.int8)
		for i in xrange(nrows) :
			vsum += sdp.sdp2np(lst[i])

		above_thresh = np.where( vsum > nrows/2. )[0]

		rv = SDP(nbits) #all zeros
		#set to 1 all bits above the threhold
		if len(above_thresh) > 0 : sdp.set_by_ixs(rv,above_thresh)
		if nrows % 2 == 0 : #even
			ties = np.where( vsum == nrows/2 )[0] #which cols are even
			size = len(ties)
			if size > 2 :#more than 2 ties, pick randomly 50%, which to set to 1
				rand_ixs = np.random.choice(ties, size=int(np.round(0.5 * size)), replace=False )
				sdp.set_by_ixs(rv,rand_ixs)

		return rv



	#Bundling, set composition, superposition, merge
	@staticmethod
	def bundle2(lst):
		nrows = len(lst)
		if nrows < 2 : raise Exception("Need more than one SDP when bundling")
		nbits = len(lst[0])
		#fill the BMAP2D with the list of SDP's
		tmp = lst[0] #collect all bitstrings
		for i in xrange(1,nrows) :	tmp = tmp.cat(lst[i])
		vs = BMap2D(nrows=nrows,nbits=nbits)
		vs.set(tmp)

		vsum = vs.count_ones(axis='cols')
		above_thresh = np.where( vsum > nrows/2. )[0]
		rv = SDP(nbits) #all zeros
		#set to 1 all bits above the threhold
		if len(above_thresh) > 0 : sdp.set_by_ixs(rv,above_thresh)
		if nrows % 2 == 0 : #even
			ties = np.where( vsum == nrows/2 )[0] #which cols are even
#			print "ties:%s" % (ties)
			size = len(ties)
			if size > 2 :#more than 2 ties, pick randomly 50%, which to set to 1
				rand_ixs = np.random.choice(ties, size=int(np.round(0.5 * size)), replace=False )
				sdp.set_by_ixs(rv,rand_ixs)
			else : #!fixme
				if size > 0 : sdp.set_by_ixs(rv,ties[0]) #switch one !!

		return rv


	@staticmethod
	def spatter_dense(lst): #high-level for associative memory
		rv = lst[0]
		for i in xrange(len(lst)) : rv |= lst[i]
		return rv

	@staticmethod
	def spatter_sparse(lst): #low-level for new concepts
		nrows = len(lst)
		if nrows < 2 : raise Exception("Need more than one SDP")
		nbits = len(lst[0])
		#fill the BMAP2D with the list of SDP's
		tmp = lst[0]
		for i in xrange(1,nrows) :	tmp = tmp.cat(lst[i]) #!!!
		vs = BMap2D(nrows=nrows,nbits=nbits)
		vs.set(tmp)
		vsum = vs.count_ones(axis='cols')

		above_thresh = np.where( vsum > nrows/1.5 )[0]
		rv = SDP(nbits) #all zeros
		if len(above_thresh) > 0 : sdp.set_by_ixs(rv,above_thresh)
		return rv

	@staticmethod #set the bits specified by the indexes to 1
	def set_by_ixs(val, ixs):
		for i in ixs : val[i] = sdp.ONE

	@staticmethod #get the bits specified by the indexes as SDP
	def get_by_ixs(val, ixs):
		return SDP([ val[i] for i in ixs ])


	@staticmethod #not good
	def rand_sparse(size,sparsity=0.02):
		cnt = int( np.round( size * sparsity ))
		tmp = np.zeros(size)
		tmp[:cnt] = 1
		np.random.shuffle(tmp)
		return SDP(list(tmp))

	@staticmethod
	def other_rand(size): #!fixme test for speed
		return SDP(list(np.random.randint(0,2,size)))

	@staticmethod
	def rand(size=nbits):
		return SDP([np.random.randint(0,2) for _ in xrange(size)])

	#given bmap2d of generated patterns, try to generate the next
	# random pattern a hamming distance apart
	@staticmethod
	def bounded_rand(size, mem, ix, trys=20, low=0.45, high=1):
		rv = sdp.rand(size)
		for i in xrange(trys):
			sdp.random_trials += 1
			counts = ( mem[:ix-1,:] ^ rv.dup(ix) ).count_ones(axis='rows')
			if np.all( counts > (size * low) ) and np.all( counts < (size * high) ) : return rv
			rv = sdp.rand(size)
		return rv

	@staticmethod
	def flip_bits(sdp_val, bits):
		if isinstance(bits, int) :
			bits = np.random.choice(sdp.nbits, bits, replace=False)
		for i in bits : sdp_val[i] = not sdp_val[i]

	@staticmethod
	def imgshow(sdp_val, width=100):
		ary = np.fromstring(sdp_val.unpack(), dtype=np.bool).astype(np.int8)
		view = ary.view()
		view.shape = 100, 100
		plt.imshow(view, cmap='Greys', interpolation='nearest', aspect='auto')
		plt.tight_layout()
		plt.show()




"""
	Semantic Distributed Pointer
"""

class SDP(bitarray):

	def __init__(self, *args, **kwargs):
		super(self.__class__, self).__init__()
		if len(args) > 0 and isinstance(args[0], int) : self.setall(0)

#	def __new__(cls, *args, **kwargs):
#		bitarray.__new__(cls, *args, **kwargs)
#		if len(args) > 0 and isinstance(args[0], int) : cls.setall(0)

	def one_idxs(self):
		idxs = self.search(bitarray("1"))
		return np.array(idxs,dtype=np.uint16)

	def zero_idxs(self):
		idxs = self.search(bitarray("0"))
		return np.array(idxs,dtype=np.uint16)

	@property
	def density(self) : return self.count() / float(self.length())

	def __add__(self, rhs) : return sdp.bundle([self,rhs])
	def __mul__(self, rhs) : return sdp.bind(self,rhs)
	def __div__(self, rhs) : return sdp.unbind(self,rhs)
	def __mod__(self, rhs) : return sdp.dist(self, rhs)
	def __lshift__(self, cnt):
		return self[cnt:] + type(self)('0') * cnt
	def __rshift__(self, cnt):
		return type(self)('0') * cnt + self[:-cnt]
	def __repr__(self) :
		if len(self) < 100 : return self.to01()
		return self.to01()[:100] + '...'

	#because we overrode those for composition ...
	def dup(self, rhs): return super(self.__class__, self).__mul__(rhs)
	def cat(self, rhs): return super(self.__class__, self).__add__(rhs)



