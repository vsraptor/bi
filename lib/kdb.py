from dyn_memory import DynMemory
from bi import sdp, SDP
from lexicon import lex
from hashed_lex import *
from bi_utils import *
from utils import get_size

from functools import wraps
from collections import OrderedDict

__VERSION__ = '0.1'

#decorators for faster memoized best_match : .bm_soa()
def fast(fun):
	cache = {} # test engine_bi: 189 items/256772 bytes
	@wraps(fun)   # ~40s => ~6s
	def wrap(self, sdp_val):
		b = sdp_val.tobytes()
		if b not in cache :
			cache[b] = fun(self,sdp_val)
		return cache[b]
	return wrap

#mem usage depends on hbits_cnt, default ~ <10% of @fast
def low_mem(fun):
	cache = {}
	@wraps(fun)
	def wrap(self, sdp_val):
		b = sdp.get_by_ixs(sdp_val, self.bm_rand_bits).tobytes()
		if b not in cache :
			cache[b] = fun(self, sdp_val)
		return cache[b]
	return wrap

#Last Recently Used expiration cache.
def lru(cache_size=50) :
	def lru_wrap(fun):

		tick = [0]
		cache = {}
		rev = {} #reverse idx : tick => key

		@wraps(fun)
		def wrap(self, sdp_val):
			tick[0] += 1
			b = sdp_val.tobytes()
			if b not in cache : #new element
			 	cache[b] = [ fun(self,sdp_val), tick[0] ]
				rev[tick[0]] = b
			else : #update element tick
				del rev[ cache[b][1] ]
				rev[tick[0]] = b
				cache[b][1] = tick[0]

			#delete the least used if full
			if len(cache) > cache_size :
				min_key = min(rev)
				del cache[rev[min_key]]
				del rev[min_key]

			return cache[b][0]

		return wrap

	return lru_wrap


class KDB :

	builtins = [ '=', 'is', '+', '-', '*' , '/' ]

	max_terms = 13 #15 save two for arity&type
	fun_sym = '$0'
	arity_sym = '$arity'

	#types ...
	type_sym = '$type'
	ATOM = 0
	VAR = 1
	STRUCT = 2

	def __init__(self, items=50, nbits=sdp.nbits, cups=None, hbits_cnt=int(sdp.nbits * 0.1)):
		self.heads = DynMemory(items=items, nbits=nbits)
		self.hbixs = [] #pointer-ids for head =[ixs]=> body sdps
		self.bodys = DynMemory(items=items*2, nbits=nbits)
		#hold internal symbols, like sdp slots: $0 .. $20, vars : @1 ..
#		self.syms = BSHLex(items=50, nbits=nbits, hbits_cnt=hbits_cnt)
		self.syms = lex(items=50, nbits=nbits)

		#grounding atoms
#		self.atoms = BSHLex(items=100, nbits=nbits, hbits_cnt=hbits_cnt)
		self.atoms = lex(items=100, nbits=nbits)
		#list of cleanup memories used to resolve SDP => syms
		self.cups = [ self.syms, self.atoms ]
		#additional cleanup memories holding user-atoms
		if cups is not None and not isinstance(cups, list) : cups = [cups]
		if cups is not None : self.cups += cups

		#MEMOIZE : bit-sampling, which bits to pick
		self.bm_rand_bits = np.random.choice(sdp.nbits, hbits_cnt, replace=False)

		#var names are build by @global-counter _ local-counter
		self.head_cnt = counter()
		#indexed by clause-head-functor
		self.hfidx = {} #... for faster search, 30% speedup
		self.init_lexes()

	def init_lexes(self):
		self.syms.add_items(['true', 'false', KDB.arity_sym])
		#used for role-names in a SDP
		slots = [ '$'+str(i) for i in xrange(KDB.max_terms+1) ]
		self.syms.add_items(slots)
		#substitution variable names
		varx = [ '@'+str(i) for i in xrange(KDB.max_terms+1) ]
		self.syms.add_items(varx)
		self.syms.add_items(KDB.builtins)


	def clean_db(self) :
		self.heads.erase()
		self.hbixs = []
		self.bodys.erase()

	#no links to bodys memory
	def is_fact(self,ix) : return len(self.hbixs[ix]) == 0

	#returns clause-head by IDx
	def head_sdp(self, ix) : return self.heads.mem[ix,:].bmap
	#returns clause-body by IDx
	def body_sdp(self, ix) : return self.bodys.mem[ix,:].bmap
	#returns clause-body by head-IDx
	def hb_sdp(self, clause_ix, nth=0) : return self.bodys.mem[ self.hbixs[clause_ix][nth],:].bmap
	#given n-th position return the index of a clause-body
	def nth_body_ix(self, clause_ix, nth) : return self.hbixs[clause_ix][nth]
	#how many terms a clause have ?
	def body_count(self, clause_ix) : return len(self.hbixs[clause_ix])


	#Best match symbol, atom or user-atom. Memoized.
	# @fast : unlimited growth of the cache
	# @lru(cache_size) : less memory requirments but slower
	# @low_mem : memory use for depends on self.hbits_cnt, experimental

#	@lru(cache_size=100)
#	@low_mem
	@fast
	def bm_soa(self, sdp) :
		soa = None
		for cup in self.cups :
			soa = cup.bm(sdp)
			if soa is not None : return soa
		return soa

	def get_atom(self, atom) :
		for cup in self.cups[1:] : #skip syms-cup
			if cup.exists(atom) : return cup.g(atom)
		return None

	def exists_user_atom(self, atom):
		for cup in self.cups[2:] : #skip syms and atoms cups
			if cup.exists(atom) : return True
		return False

	def avivi_atom(self, atom):#auto-vivify : create if non-existant
		if not (self.atoms.exists(atom) or self.exists_user_atom(atom)) : self.atoms.add(atom)
	def avivi_var(self, var):#create if non-existant
		if not self.syms.exists(var) : self.syms.add(var)

	#Iterator over head of clauses
	def head_iter(self, low=0, sdp=False):
		current = low; high = self.heads.last_ix
		while current <= high:
			if not sdp : yield current
			else : yield self.head_sdp(current)
			current += 1

	#Iterator over body of a clause
	def body_iter(self, clause_ix, sdp=False):
		for ix in iter(self.hbixs[clause_ix]) :
			if sdp :	yield self.body_sdp(ix)
			else : yield ix

	#backtrack generator
	def backtrack(self, clause_ix, sdp=False, low=0):
		high = len(self.hbixs[clause_ix])
		i = 0
		while i >= low and i <= high :
			#return index or SDP
			rv = i if not sdp else self.body_sdp(self.hbixs[i])
			cond = yield rv
			if cond : i += 1 #forward
			else	  : i -= 1 #backward

	#if we have predicate-index, then return list of head-clause-ixs
	# ... used for looping only the heads with that functor, instead of the whole KDB
	def head_pred_lst(self, head_functor):
		if head_functor not in self.hfidx : return []
		return self.hfidx[head_functor]

	#extract all the symbols from an SDP into a list
	# 1011100..... =>  [ functor, vv1, vv2, vv3, ... ]
	def sdp2syms(self, sp) :
		syms = []; i = 0;
		while True : #SDP to syms
			slot_sdp = self.syms.g(slot(i))
			#search all the cleanup memories for this symbol
			sym = self.bm_soa( sdp.unbind(slot_sdp, sp) )
			if i >= KDB.max_terms or sym is None :	break
			syms.append(sym)
			i += 1

		#!more correct : return [tuple(syms)]
		return syms # .. but this seems to work

	# f(t1,t2,t3,...) : given { functor: f, terms : [ t1, t2, t3, ...] }, return SDP
	def struct2sdp(self, struct, cnt, preserve_vars=False, var_kind='') :
		terms = []
		vv = []

		#create ground atoms if nececary
		self.avivi_atom(struct['fun'])
		# a FACT
		if 'terms' not in struct or len(struct['terms']) == 0 :
			return self.syms.g(slot(0)) * self.atoms.g(struct['fun'])

		# a RULE-CLAUSE
		for term in struct['terms'] :
			if is_var(term) :
				var = 'err!'
				#should we create new var or reuse old one
				if term in self.used_vars :
					var = self.used_vars[term]
				else :
					if preserve_vars : var = term
					else :
						i = cnt.next()
						var = var_name(i, kind=var_kind)
					self.used_vars[term] = var

				terms.append(var)

			else : #create atom if it does not exists already
				self.avivi_atom(term)
				terms.append(term)

		#build the SDP : $arity:? + $0:v1 + $1:v2 + $2:v3 + ...
		for i, item in enumerate( [struct['fun']] + terms) :
			if is_var(item) : #vars and atoms are stored in different lexers
				self.avivi_var(item)
	 			vv.append( sdp.bind(self.syms.g(slot(i)), self.syms.g(item)) )
			else :
				vv.append( sdp.bind(self.syms.g(slot(i)), self.get_atom(item)) )

		#bundle the bindings
		return self.syms.bundle(vv)


	def add_struct(self, struct, cnt) :
		if isinstance(struct, dict) :
			six, _TF = self.stucts.add( self.struct2sdp(struct, cnt) )
		else :
			six, _TF = self.stucts.add(struct)
		return six

	def add_head(self, struct, cnt) :
		hix, _TF = self.heads.add( self.struct2sdp(struct, cnt) )
		return hix

	def add_body(self, structs, cnt):
		ixs = []
		for s in structs :
			ix, _TF = self.bodys.add( self.struct2sdp(s, cnt) )
			ixs.append(ix)
		return ixs

	def add_clause(self, head, body=None):
		#used for var-name generation
		#vcnt = var_counter(head_ix=self.head_cnt.next())
		vcnt = counter(high=1000)
		self.used_vars = {} #so we dont repeat vars
		hix = self.add_head(head, vcnt)
		#add item to the head-functor-index
		fun = head['fun']
		if fun not in self.hfidx : self.hfidx[fun] = []
		self.hfidx[fun].append(hix)

		if body is None :#its a fact
			self.hbixs.append([])
		else :
			bixs = self.add_body(body, vcnt)
			self.hbixs.append( bixs )
		return hix


#---------------- LISTING ----------------------------------------

	#return string representation of structure stored in SDP
	def struct_str(self, ix, mem ):

 		struct_sdp = mem.mem[ix,:].bmap

		fun = self.atoms.bm( self.syms.g('$0') * struct_sdp)
		i = 1
		terms = []
		while True :
			term = self.bm_soa( sdp.unbind( self.syms.g(slot(i)), struct_sdp) )
			if i >= KDB.max_terms or term is None : break
			terms.append(str(term))
			i += 1

		#atom
		if len(terms) == 0 : return fun
		return fun + '(' + ','.join(terms) + ')'

	def clause_str(self,ix):
		head = self.struct_str(ix, mem=self.heads)
		bodys = []
		if len(self.hbixs[ix]) > 0 : #if not a fact
			for bix in self.hbixs[ix] :
				bodys.append( self.struct_str(bix, mem=self.bodys) )

		if len(bodys) == 0 : return head + '.'
		return head + ' :- ' + ', '.join(bodys) + '.'

	#list the program stored in KDB
	def listing(self):
		string = ''
		for cix in self.head_iter() :
			string += "%s> " % cix + self.clause_str(cix) + "\n"
		return string

	def list_structs(self):
		string = ''
		for cix in xrange(self.structs.ix + 1) :
			string += "%s> " % cix + self.struct_str(cix, mem=self.structs) + "\n"
		return string


	def __str__(self): return self.listing()





