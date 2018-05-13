import re
import logging as log
log.root.setLevel(log.DEBUG)
log.getLogger("lepl").setLevel(log.ERROR)

from bi import *
from lexicon import *
from lepl import *

"""

	This module contains the basic structures to build the Bi system.
	Hierarchial BB-structure holds the Symbols, separate bit-array memory store all SDP.

	Basic ops :
		probe : returns back the name of the "opposite-binder", if it exists. Bind related op.
		contain : checks if the value exist in the structure. Bundle related op.
		match : do the values match, simply compare the SDPs
		update : ...

	At the leafs of hierarchy are the Atom which is the basic "unstructured" item/atom that is used to build a structure.
	The ubiquitos structure is the Chunk or BuBi.
	Chunk is recursive Bindle/Bundles structure. We preserve structural information for the chunks i.e.
	the chunk is composition of the instantiated objects of Bundle and Bindle classes.
	 > Bindle is v1 * v2 * v3 * ...
	 > Bundle is v1 + v2 + v3 + ...


	!!! self.atoms : has to be array, the order of the items has to be preserved. So that .mk_uid() returns consistent results.

	In addition this module supports :

		- multilevel CUP memory i.e. separate CUP for every level of expressions
		- Additoinal shorthand structures : Key-Value List, Predicates, TinyArray, Sequence ...

"""

def override(superClass):
	def method(func):
		getattr(superClass,method.__name__)
		return method

def refresh(bubi):
	for p in bubi.parents : p.update()
	#we don't want to process the same parent twice if they are crossreferenced
	ps = set( p for p in bubi.parents if not p.is_top )
	if len(ps) > 0 :
		for p in ps : p.update()
		refresh(p)


class Base(object):

	@property
	def sdp(self):
		log.debug("v:%s" % self.uid)
		return self.cup.g(self.uid)

	#temporarily disable cached, to regenerate the .sdp
	def refresh(self):
		#self.uid = self.mk_uid() i.e doesnt create new item but reuses the old one
		cached = self.cached
		self.cached = False
		self.cup.s(self.uid, self.sdp)#sdp is regenerated in this case
		self.cached = cached

	#Match is common across objects ... match the SDPs
	def match(self, p):
		if p == self.sdp : return True
		return False

#Single SDP value always added to CUP mem
class Atom(Base):

	def __init__(self, uid, cup, sdp_value=None, reuse=True, lvl=0, depth=0, parent=None):
		self.cup = cup #!fix me if cup is list then use LVL
		self.uid = uid
		self.lvl = lvl
		self.depth = depth
		self.parents = [parent]

		if self.cup.exists(self.uid) :
			if not reuse : raise Exception(">%s< already exists in CUP" % self.uid)
		else: self.cup.add(self.uid, sdp_value)

	def set_parent(self, parent, ix=0): self.parents[ix] = parent

	def contain(self, p): return self.match(p)
	def probe(self, p) :
		if self.match(p) : return self.uid
		return 'null'

	def __repr__(self):
 		lead = (self.depth - self.lvl) * "  "
		return "%s%s|%s: %s" % (lead, self.lvl, self.uid, self.sdp)


#Bindle and Bundle share the probe & contain methods, so far only .sdp generation differ
class Chunk(Base):

	def __init__(self, atoms, cup, uid=None, cached=True, reuse=True, lvl=0, depth=0, parent=None):
		if not isinstance(atoms, list) : raise Exception("Chunk creation: Expecting -atoms- aslist!")
		self.cup = cup
		self.atoms = atoms
		self.lvl = lvl
		self.depth = depth
		self.parents = [parent]
		self.is_top = False

		#use or create new uid
		self.uid = uid if uid else self.mk_uid()

		#parents used for propagating updates, up the chain
		for v in self.atoms : v.set_parent(self)

		#if TRUE on init we set it to False to force generation of the SDP, .sdp() always check for this flag
		# .. this way it is cached in memory for subsequeent calls
		self.cached = False
		if cached : #see: cached not self.cached
			if self.cup.exists(self.uid) :
				if not reuse : raise Exception(">%s< already exists in CUP" % self.uid)
			else : self.cup.add(self.uid, self.sdp)
			self.cached = True

	@property
	def size(self) : return len(self.atoms)

	def mk_uid(self): raise NotImplementedError('Define uid creation method')
	def set_parent(self, parent, ix=0): self.parents[ix] = parent
	#This is the expression top-level e.g. symbol that represent this expression.
	#this the "base-line" atom for the next LAYER
	def set_top(self): self.is_top = True

	#given index set the specified item to a new value and refresh&rename
	def set_item(self, ix, val) :
		 self.atoms[ix] = val
		 self.refresh()
		 #fix the uid-instances
		 new_uid = self.mk_uid()
		 self.cup.rename(self.uid, new_uid)
		 self.uid = new_uid

	def probe(self, p):
		if isinstance(p,str): p = self.cup.g(p)
		res = sdp.probe(p, self.sdp)
		rv = self.cup.best_match(res)
		if rv is None : return 'null'
		return rv

	def contain(self,p) :
		if self.probe(p) == 'null' : return False
		return True

	def __repr__(self):
 		lead = (self.depth - self.lvl) * "  "
#		rv = "%s%s|%s.%s:\n" % (lead,self.lvl, type(self).__name__,self.uid)
		rv = "%s%s|%s:\n" % (lead,self.lvl,self.uid)
		for v in self.atoms :
			rv += v.__repr__() + "\n"
		return rv.rstrip()


class Bindle(Chunk):

	def mk_uid(self):
		uid = '*'
		for v in self.atoms : uid += v.uid
		return uid

	@Chunk.sdp.getter
	def sdp(self):
		log.debug("bi:%s  add:%s" % (self.uid, self.cached))
		#don't calc if already in memory
		if self.cached: return self.cup.g(self.uid)
		rv = self.atoms[0].sdp
		for p in self.atoms[1:]:	rv = sdp.bind(rv, p.sdp)
		return rv

class PermutedBindle(Chunk):

	def __init__(self, uid, atoms, cup, op, pmx, cached=True, reuse=True, lvl=0, depth=0):
		self.op = op
		self.pmx = pmx
		super(self.__class__, self).__init__(uid=uid, atoms=atoms, cup=cup, cached=cached, reuse=reuse, lvl=lvl, depth=depth)

	#!fixme: sort
	def mk_uid(self):
		uid = self.op
		for v in self.atoms : uid += v.uid
		return uid

	@Chunk.sdp.getter
	def sdp(self):
		log.debug("pbi:%s  add:%s" % (self.uid, self.cached))
		#don't calc if already in memory
		if self.cached : return self.cup.g(self.uid)
		arg1 = self.atoms[0].sdp
		arg2 = self.atoms[1].sdp
		op = self.op

		#binding OR probing
		fun = sdp.pbind
		if op.find('<') != -1 : fun = sdp.pprobe

		io = op.strip('><')
		num = None if io == '*' else int(io)
		#if num then roll() else permute()
		if num : rv = fun(arg1, arg2, num)
		else : rv = fun(arg1, arg1, self.pmx)

		return rv

class Bundle(Chunk):

	def mk_uid(self):
		uid = '+'
		for v in self.atoms : uid += v.uid
		return uid

	@Chunk.sdp.getter
	def sdp(self):
		log.debug("bu:%s  add:%s" % (self.uid, self.cached))
		#don't calc if already in memory
		if self.cached : return self.cup.g(self.uid)
		return sdp.bundle([ p.sdp for p in self.atoms])


class ComplexChunk(Chunk):

	def __init__(self, atoms, cup, uid=None, cached=True, reuse=True, lvl=0, depth=0, parent=None):
		assert len(atoms) < 20, "Complex chunks can not be bigger than 20 elements !!"
		super(self.__class__, self).__init__(atoms=atoms, cup=cup, uid=uid, cached=cached, reuse=reuse, lvl=lvl, depth=depth, parent=parent)


#k1 * v1 + k2 * v2 + ...
class KVList(ComplexChunk):

	def mk_uid(self):
		uid = '%'
		for v in self.atoms : uid += v[0].uid + ':' + v[1].uid + ','
		return uid

	@Chunk.sdp.getter
	def sdp(self):
		log.debug("kvl:%s  add:%s" % (self.uid, self.cached))
		#don't calc if already in memory
		if self.cached : return self.cup.g(self.uid)
		return sdp.bundle([ sdp.bind( p[0].sdp, p[1].sdp ) for p in self.atoms])

	def g(self, key):
		bm = self.probe(self.cup.g(key))
		if bm == 'null' : return None, None #!fix:null
		return bm, self.cup.g(bm)


#pred(k1:v1, k2:v2) => predicate + k1 * v1 + k2 * v2 + ...
class Clause(ComplexChunk) :

	def mk_uid(self):
		uid = '>%' + self.atoms[0].uid
		for v in self.atoms[1:] : uid += v[0].uid + ':' + v[1].uid + ','
		return uid

	@Chunk.sdp.getter
	def sdp(self):
		log.debug("pred:%s  add:%s" % (self.uid, self.cached))
		#don't calc if already in memory
		if self.cached : return self.cup.g(self.uid)
		return sdp.bundle([ self.atoms[0].sdp ] + [ sdp.bind( p[0].sdp, p[1].sdp ) for p in self.atoms[1:] ])


#[v1,v2,v3,v4,....] => 1 * v1 + 2 * v2 + ...
class TinyAry(ComplexChunk) :

	def __init__(self, atoms, cup, uid=None, cached=True, reuse=True, lvl=0, depth=0, parent=None):
		if not cup.exists('20') : #add index-syms for use to access elems
			cup.add_items([ str(i) for i in xrange(20) ])
		super(self.__class__, self).__init__(atoms=atoms, cup=cup, uid=uid, cached=cached, reuse=reuse, lvl=lvl, depth=depth, parent=parent)

	def mk_uid(self):
		uid = '@'
		for v in self.atoms : uid += v.uid
		return uid

	@Chunk.sdp.getter
	def sdp(self):
		log.debug("ary:%s  add:%s" % (self.uid, self.cached))
		if self.cached : return self.cup.g(self.uid)
		return sdp.bundle([ sdp.bind( self.cup.g(str(i)), p.sdp ) for i,p in enumerate(self.atoms) ])

	#get item by index
	def g(self, ix):
		bm = self.probe(self.cup.g(str(ix)))
		if bm == 'null' : return None, None #!fix:null
		return bm, self.cup.g(bm)

class Sequence(ComplexChunk) : pass
#
class Pair(Bindle) : pass

#parses expression string and converts it to BB structure
class BBExpr(object):

	def __init__(self, cup, pmx, log_level=log.DEBUG):

		log.root.setLevel(log_level)

		self.cup = cup
		self.grammar = None
		self.expr = None #last expression
#		self.h = Hashids()
		self.pmx = pmx #we need permutation matrix in case of pbind 
		self.build_grammar()

	#currently uid embeds the op in the name. Ex: a*b, b*>d, thus it cant be referenced easy from other exprs
	#.. may be we should use mnemonics, a_bi_b vs a*b, b_pbi_d ...
	def uid(self, op, lst) :
		rv = op

		for el in lst :
			if isinstance(el, str) : rv += el; continue
			if isinstance(el, Bundle) : rv += el.uid; continue
			if isinstance(el, Bindle) : rv += el.uid; continue
			if isinstance(el, PermutedBindle) : rv += el.uid; continue
		return rv

	# v1 op v2 v3 v4 ... => op v1 v2 v3 v4 ....
	def to_infix(self, lst) : return lst[1], [lst[0]] + lst[2:]

	def bubi(self, op, lst, lvl=0, depth=0):
		print "op,lvl: %s %s" % (op, lvl)
		atoms = []
		#allowing multi-level CUP
		cup = self.cup
		atoms_cup = self.cup
		if isinstance(self.cup, lexes) :
			if depth > self.cup.nlex : raise Exception("Expression 'depth' is bigger than the number of available CUP lexicons : %s != %s" % (depth, self.cup.nlex) )
			cup = self.cup.lexes[lvl-1]
			atoms_cup = self.cup.lexes[0]

		for var in lst: #loop over the arguments
			if isinstance(var, str) :
				val = Atom(var, atoms_cup, reuse=True, lvl=lvl-1, depth=depth)
			else : val = var
			atoms.append(val)
		if op == '+' : return Bundle(atoms, cup, reuse=True, lvl=lvl, depth=depth)
		if op == '*' : return Bindle(atoms, cup, reuse=True, lvl=lvl, depth=depth)
		if re.search(r'[><]', op) : return PermutedBindle(atoms, cup, op, self.pmx, reuse=True, depth=depth)

	def bindle(self, lst):
		op, atoms = self.to_infix(lst)
		return self.bubi(op, atoms)
	def permuted_bindle(self, lst):
		op, atoms = self.to_infix(lst)
		return self.bubi(op, atoms)
	def bundle(self, lst):
		op, atoms = self.to_infix(lst)
		return self.bubi(op, atoms)

	def build_grammar(self):
		spaces = Token('[ \t]+')[:]
		plus = Token('\+')
		left_bracket = Token('\(')
		right_bracket = Token('\)')
		mult = Token('\*')
		bit_var = Token('[a-zA-Z0-9_!\?]+')
		op_perm = Token("[\*0-9]+>")
		op_iperm = Token("<[\*0-9]+")

		with Separator(~spaces):

			group2, expr = Delayed(), Delayed()

			parens = ~left_bracket & expr & ~right_bracket
			group1 = parens | bit_var
			mul = group1 & mult & group2 > self.bindle
			expr_perm = group1 & (op_perm | op_iperm) & group2 > self.permuted_bindle
			group2 += mul | expr_perm | group1
			add = group2 & plus & expr > self.bundle
			expr += add | group2

			line = LineStart() & expr & LineEnd()
			self.grammar = expr

	def parse(self,txt):
		return self.grammar.parse(txt.strip())[0]

	#calc depth of ast
	def depth(self, ast):
		if isinstance(ast, str): return 1
		else:
			dL = self.depth(ast[1])
			dR = self.depth(ast[2])
			return max(dL, dR) + 1

	#!fixme : add support for multilevel CUP
	def _parse_ast(self, ast, lvl=0, depth=0):
		lst = []
		op = ast[0]
		for el in ast[1:] :
			if isinstance(el, list):  lst.append( self._parse_ast(el, lvl=lvl-1, depth=depth) )
			else : lst.append(el)
		return self.bubi(op, lst, lvl-1, depth=depth)

	def parse_ast(self, ast):
		depth = self.depth(ast)
		print "depth> ", depth
		rv = self._parse_ast(ast,lvl=depth+1, depth=depth)
		rv.set_top()
		return rv

	#convert a String that looks like AST to AST-LoL i.e. add the quotes around the terms
	# "[*,a,b]"  => ['*', 'a', 'b']
	def str2ast(self, string):
		return eval( re.sub(r'([^,\[\]]+?)', r'"\1"', string.replace(' ', '')) )


#=========== greedy expr test ============================

	def build_grammar2(self):
		spaces = Token('[ \t]+')[:]
		plus = Token('\+')
		left_bracket = Token('\(')
		right_bracket = Token('\)')
		mult = Token('\*')
		bit_var = Token('[a-zA-Z0-9_!\?]+')

	#	with Separator(~spaces):

 		expr, group2 = Delayed(), Delayed()

		mul_node = bit_var & (~mult & bit_var)[1:] > Node
		add_node = bit_var & (~plus & bit_var)[1:] > Node
		node = mul_node | add_node

		parens = ~left_bracket & expr & ~right_bracket

		group1 = parens | node
		add = group1 & ~plus & group2 > Node
		group2 +=  group1 | add
		mul = group2 & ~mult & expr > Node
		expr +=  group2 | mul

		self.grammar = expr

