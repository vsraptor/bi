from lexicon import *
from dyn_memory import *

"""

	HashedLex
	Lexicon with faster-indexed best-match, but only good for exact matches 
	i.e. can not be used as cleanup memory !:(, where the match is based on similarity
	i.e. hamming distance

"""

class HashedLex(lex):

	def __init__(self, *args, **argv):
		super(self.__class__, self).__init__(*args, **argv)
		self.indx = {}


	def add(self, *args, **argv) :
		ix = super(self.__class__, self).add(*args, **argv)
		hkey = hash(self.mem.mem[ix,:].bmap.to01())
		self.indx[hkey] = self.lex_inv[ix]

	def best_match(self, pat):
		hkey = hash(pat.to01())
		if hkey not in self.indx : return None
		return self.indx[hkey]
	bm = best_match



"""

	BSHLex : BitSample Hashed Lexicon
	Use it instead of Lexicon for faster-hashed best-match.
	Good for approximate matches too i.e. can be used as cleanup memory.
	Picks randomly M-bits out of total N-bits and use it as a hash.

"""

class BSHLex(lex):

	HBITS = 1024 #hash-len, good below 1000 cup-items

	def __init__(self, *args, **kwargs):
		#How many bits from the original to use as a hash
		self.hbits_cnt = kwargs.pop('hbits_cnt', BSHLex.HBITS)
		super(self.__class__, self).__init__(*args, **kwargs)
		self.bsh = DynMemory(self.mem.items, self.hbits_cnt) #hash
		#which bits to pick
#		self.rand_bits = list(np.random.randint(0, sdp.nbits, self.hbits_cnt))
		self.rand_bits = np.random.choice(sdp.nbits, self.hbits_cnt, replace=False)

	def bshash(self, pat):#pick random fewer bits
		return  sdp.get_by_ixs(pat, self.rand_bits)
#		return self.mem.mem[ix, self.rand_bits].bmap

	def add(self, *args, **kwargs) :
		ix = super(self.__class__, self).add(*args, **kwargs)
		hkey = self.bshash(self.mem.mem[ix, :].bmap)
	#	self.bsh.mem[ix,:] = hkey #populate the hash-table
		self.bsh.add(hkey) #populate the hash-table, assume both in sync


	def best_match(self, pat):
		hkey = self.bshash(pat)
		counts = ( self.bsh.mem[:self.bsh.ix,:] ^ hkey.dup(self.bsh.ix+1) ).count_ones(axis='rows')
		ix = np.argsort(counts)[0] #first-smallest
		if ix is None : return None
		if ix > self.mem.ix : print " ** no match in the lexicon ix: %s ? **" % ix; return None
		#!fixme: is the match within the threshold
		#if not sdp.sim(hkey, self.bsh.g(ix), nbits=self.hbits_cnt, thresh=0.45) : return None #hash-sim, more prob of being false
		if not sdp.sim(pat, self.g(ix)) : return None #full SDP sim, slower
		return self.lex_inv[ix]
	bm = best_match



