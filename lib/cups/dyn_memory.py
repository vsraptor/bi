from bmap2D import *
from bi import sdp, SDP

"""

	Dynamicaly growing 2D bitmap memory.
	Also supports deleting elements/rows.

"""

class DynMemory(object):

	def __init__(self, items=100, nbits=100, growth=0.1, bounded_rand=False, bm_thresh=0.42):
		self.items = items
		self.nbits = nbits
		self.growth = growth
		self.bounded_rand = bounded_rand
		self.mem = BMap2D(self.items, self.nbits)
		self.bm_thresh = bm_thresh #how close is assumed a match
		self.erase()

	@property
	def last(self): return self.mem[self.ix-1, :].bmap

	@property
	def last_ix(self): return self.ix

	def grow(self):
		items = self.growth if isinstance(self.growth, int) else int(self.items * self.growth) + 1
		print "growing:  +%s items to memory" % items
		self.items += items
		self.mem.add_rows(items)

	def add(self, pat=None):
		ix = None
		poped = False
		#if there are free items, use them instead of allocating new
		if len(self.free) > 0 :
			poped = True
			ix = self.free.pop()
		else:
			self.ix += 1
			ix = self.ix
			if self.ix >= self.items : self.grow()

		if pat is not None :
			self.mem[ ix, : ] = pat
		else :
			if self.bounded_rand :
				self.mem[ ix, : ] = sdp.bounded_rand(self.nbits, self.mem, self.mem.ix)
			else:
				self.mem[ ix, : ] = sdp.rand(self.nbits)

		if poped : return ix, False #old/reused
		return ix, True #new

	def erase(self):
		self.mem.erase()
		self.ix = -1
		self.free = [] #list of free indexes

	#put the item in the free-list for reuse
	def remove(self, ix):
		self.mem[ix,:] = 0
		self.free.append(ix)

	def add_items(self, lst) :
		for el in lst : self.add(el)

	def get(self,idx): return self.g(idx)
	def g(self, idx):	return SDP(self.mem[ idx, : ].bmap)
	def s(self, idx, value): self.mem[ idx, :] = value

	def best_topixs(self, pat, rng=1):
#		nrows = self.mem.shape[0]
		#compare the whole memory
#		counts = ( self.mem ^ pat.dup(nrows) ).count_ones(axis='rows')
		#compare just the filled memory
		counts = ( self.mem[:self.ix,:] ^ pat.dup(self.ix+1) ).count_ones(axis='rows')

		ixs = np.argsort(counts)[:rng] #first-smaller
		return ixs

	def best_ix(self, pat) :
		rv_ix = self.best_topixs(pat,rng=1)[0]
		hd = sdp.dist(pat, self.g(rv_ix))
		#is the match within the threshold
		if hd/float(self.nbits) > self.bm_thresh : return None
		return rv_ix

	def best_match(self, pat):
		ix = self.best_ix(pat)
		if ix is None : return None
		return SDP(self.mem[ix, :].bmap)

	def __repr__(self):
		return self.mem.__repr__()

	@property
	def info(self):
		s  = "Dynamic Memory :==================\n"
		s += "items:%s, max items:%s, nbits:%s\n" % (self.ix, self.items, self.nbits)
		return s



class ValuedMem(DynMemory):

		def __init__(self, *args, **kw):
			super(self.__class__, self).__init__(*args, **kw)
			self.vals = np.zeros(kw['items'])
			self.gamma = 0.9
			self.lrate = 0.1

		def update_val(self, ix, qt0, qt1, reward):
			error = (reward + self.gamma * qt1 - qt0)
			self.vals[ix] += self.lrate * error



