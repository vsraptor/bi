from dyn_memory import *
import string

"""

	Keep lexicon of generated terms, states, symbols ...
	Dynamic memory where every element-hypervector (i.e. row) have a name.

"""

class lex(object):

	def __init__(self, items=100, nbits=sdp.nbits, true_thresh=sdp.true_thresh):
		self.mem = DynMemory(items=items, nbits=nbits, bm_thresh=true_thresh)
		self.erase()
		self.erased_name = '__erased__'

	@property
	def last(self): return self.mem.last

	def add(self, name, pat=None):
		if name in self.lex : raise Exception(">%s< already exists" % name)
		ix, new = self.mem.add(pat)
		#print "add> %s[%s] new:%s" % (name, ix,new)
		self.lex[name] = ix
		#did we used new memory slot OR reused old one
		if new : self.lex_inv.append(name)
		else : self.lex_inv[ix] = name
		return ix

	def remove(self, name):
		self.mem.remove(self.lex[name])
		ix = self.lex.pop(name) #remove the old name
		#print "del> %s[%s]" % (name,ix)
		self.lex_inv[ix] = self.erased_name

	def erase(self):
		self.mem.erase()
		self.lex = {}
		self.lex_inv = []

	def add_items(self, lst) :
		for el in lst : self.add(el)

	#instantiate the specified items as global variables. Test use only.
	def items_as_vars(self, lst) :
		for i in lst :
			import __builtin__
			setattr(__builtin__, str(i), self.g(i))
			#globals()[tmp] = self.g(i)
			print i, self.g(i)

	def get(self,idn): return self.g(idn)
	def g(self, idn):
		if isinstance(idn,int) : return self.mem.get(idn)
		if idn not in self.lex : raise Exception("Item '%s' does not exist" % idn)
		return self.mem.get( self.lex[idn] )

	def s(self, name, value) : self.mem.s( self.lex[name], value)
	def set(self, name, value) : self.s(name, value)

	def exists(self, name): return name in self.lex
	def rename(self, old_name, new_name) :
		self.lex[new_name] = self.lex.pop(old_name)

	def best_match(self, pat):
		ix = self.mem.best_ix(pat)
		if ix is None : return None
		if ix > self.mem.ix : print " ** no match in the lexicon ix: %s ? **" % ix; return None
		return self.lex_inv[ix]
	bm = best_match

	def __contains__(self, key) : return key in self.lex

	def __getitem__(self, key) : return SDP(self.mem.mem[ self.lex[key], : ].bmap)
	def __setitem__(self, key, name) :
		if name == 0 : self.add(key)
		else : self.add(key,name)

	def __repr__(self):
		s = ''
		for name in sorted(self.lex, key=self.lex.get):
			s += "% 15s : %s ...\n" % (name, self.get(name)[:100] )
		return s

	#generate random list of hypervectors, name them from 'a' to 'z'
	def az(self): self.add_items(list(string.lowercase))
	#add 0&1 symbols to the lexicon
	def nf(self):
		self.add('null', sdp.null(self.mem.nbits))
		self.add('full', sdp.full(self.mem.nbits))

	#symbols used as special cases
	def syms(self):
		self.add_items(['?', '!', '$', '%' , '@' ])

	def rand_items(self, cnt=10):
		for i in xrange(cnt):
			name = 'rand' + str( np.random.randint(0,100000000) )
			self.add(name)

	#===================== sdp shortcuts ======================================================


	def bind(self, x, y=None) :
		if isinstance(x, str) : x = self.get(x)
		if isinstance(y, str) : y = self.get(y)
		return sdp.bind(x,y)

	def probe(self, x, y) :
		a = x; b = y
		if isinstance(x, str) : a = self.get(x)
		if isinstance(y, str) : b = self.get(y)
		return sdp.probe(a,b)

	def bundle(self, lst) :
		sdp_lst = []
		for item in lst :
			if isinstance(item, str) : sdp_lst.append( self.get(item) )
			else: sdp_lst.append(item)
		return sdp.bundle(sdp_lst)

	def pbind(self, x, y, p) :
		a = x; b = y
		if isinstance(x, str) : a = self.get(x)
		if isinstance(y, str) : b = self.get(y)
		return sdp.pbind(a,b,p)

	def pprobe(self, x, y, p) :
		a = x; b = y
		if isinstance(x, str) : a = self.get(x)
		if isinstance(y, str) : b = self.get(y)
		return sdp.pprobe(a,b,p)


#List of lexicons. Used for hierarchial structures
class lexes(object):

	def __init__(self, nlex=3, items=100, nbits=sdp.nbits):
		self.nlex = nlex
		self.lexes = []
		for i in range(self.nlex) :
			self.lexes.append(lex(items, nbits))


