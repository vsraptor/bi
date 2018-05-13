import logging as log
log.root.setLevel(log.DEBUG)

from bi import *
from encoders.scalar_encoder import *

"""

	Mapping bit-encoded Integer to SDP space and preserving similarity
	i.e. hamming distance between numbers are preserved after mapping
	at the same time generated SDPs are still 50% away from 
	all the other SDP-symbols/atoms in the system.
	And the biggest benefit is that it can be used as dynamic cleanup memory.

	Keep in mind that if the integer-range you choose is bigger the 
	encoding/decoding would become approximate. That is to be expected.

	Info: In a similar manner we can build dynamic cleanup memory for other types 
	of data such as Categories, Dates, Lambdas/Function based,
	Hidden-Structured-data independend of SDP itself (see Splice-encoder).

"""

class CUPInteger(object):

	def __init__(self, vmin=0, vmax=1000, width=5000, sdp_map=None, true_thresh=sdp.true_thresh, bm_max_iter=None ):
		self.se = ScalarEncoder(minimum=vmin, maximum=vmax, width=width, nbits=sdp.nbits)
		self.true_thresh = true_thresh
		#how long to search for best-match value, before giving up
		self.bm_max_iter = np.log2(vmax) + 3 if bm_max_iter == None else bm_max_iter
		self.sdp_map = sdp_map
		if self.sdp_map is None : self.sdp_map = sdp.rand()
		#used to find best match
		self.vmin_sdp = self.encode_sdp(vmin)
		self.vmax_sdp = self.encode_sdp(vmax)

	#Reusing Scalar encoder functionality from my Numenta project
	def encode(self, value): return self.se.encode(value)
	def decode(self, value): return int(self.se.decode(value))

	#encoded =map=> 50% dense
	def encode_sdp(self, int_value): return sdp.bind( SDP(self.encode(int_value)) , self.sdp_map )
	esdp = encode_sdp

	def decode_sdp(self, sdp_value)  : return self.decode( sdp.bind(sdp_value, self.sdp_map))
	dsdp = decode_sdp

	#simulating lex-get
	def get(self, value):
		try :	val = int(value)
		except ValueError : return None
		return self.encode_sdp(val)
	g = get

	#searches for the closest value to this noisy sdp
	def search(self, noisy_sdp, low, high,i) :
		zrange = (high-low)
#		print "----\n", low, high, zrange

		if zrange <= 3 : #got it
			dists = [ sdp.dist(noisy_sdp, self.encode_sdp(n)) for n in xrange(low,high+1) ]
			ix = dists.index(min(dists))
			return low+ix, dists[ix] # value, distance

		#search exausted, not found i.e max distance
		if i >= self.bm_max_iter : return None, sdp.nbits

		#calc the "index" of the quartiles
		i25 = int(low + zrange*0.25); i50 = int(low + zrange*0.5); i75 = int(low + zrange*0.75)

		#how far is the sdp to the quartiles
		q25 = sdp.dist(noisy_sdp, self.encode_sdp(i25))
		q50 = sdp.dist(noisy_sdp, self.encode_sdp(i50))
		q75 = sdp.dist(noisy_sdp, self.encode_sdp(i75))

		#shrink the search frame
		if   q25 <= q50 <= q75 : high = i50
		elif q25 >= q50 >= q75 : low = i50
		elif q25 > q50 < q75 :
			low = i25; high = i75
		# .... and do it again with adjusted range
		return self.search(noisy_sdp, low, high, i+1)

	def best_match(self, sdp_value) :
		#search the mapped space
		value, dist = self.search(sdp_value, self.se.vmin, self.se.vmax, 0)
		if dist/float(sdp.nbits) > self.true_thresh : return None
		return str(value) #we return symbol not an integer

	bm = best_match #CUP best match

	def exists(self, value):
		try :	val = int(value)
		except ValueError : return False
		if val >= self.se.vmin and val <= self.se.vmax : return True
		return False

	#you can not add new items in this CUP, all items are predetermined
	def add(self, value): return self.exists(value)

