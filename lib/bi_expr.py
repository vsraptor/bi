import logging as log
log.getLogger("lepl").setLevel(log.ERROR)
from lepl import *
from bi import *
from lexicon import *
import string
import re


"""
	Simple parser for Bi-expression languge.
	The idea is at some point this to grow to full fledged language.

"""

import operator
ops = {
	'>': operator.gt, '<': operator.lt,
	'>=': operator.ge, '<=': operator.le,
	'==': operator.eq, '!=' : operator.ne
}

def compare(inp, opr, out): return ops[opr](inp, out)
def true(): return Value( ('val', True), ('vtype', 'bool') )


class BiNode(Node):

	@property
	def children(self): return self._Node__children

class Variable(BiNode):

	mem = None

	def __init__(self, lst):
		super(self.__class__, self).__init__(lst)
		if lst[:2] == '@@' and not self.mem.exists(lst[2:]) : self.mem.add(lst[2:])

	@property
	def name(self): #var name can start with @ or @@
		tmp = self.children[0]
		return tmp[ tmp.rfind('@') + 1 : ]

	@property
	def sdp(self): return self.mem.g(self.name)

	def assign(self, value) : self.mem.s(self.name, value)

	def process(self, parser):
		return Value(('val', self.sdp), ('vtype', 'sdp') )


class BB(BiNode):

	def pre_process(self, parser):
		vals = []
		for c in self.children :
			if isinstance(c, (str,int,float)) : el = c
			else : el = c.process(parser)
			log.debug('----------')
			log.debug(el)
			vals.append( el )
		log.debug('----------')
		return vals

class Bind(BB):

	def process(self, parser):
		vals = self.pre_process(parser)

		if vals[0].vtype[0] == 'sdp' :
			rv = sdp.bind(vals[0].val[0], vals[1].val[0])
			return Value(('val', rv), ('vtype', 'sdp'))

		if vals[0].vtype[0] == 'num' :
			rv = vals[0].val[0] * vals[1].val[0]
			return Value(('val', rv), ('vtype', 'num'))

class Bundle(BB):

	def process(self, parser):
		vals = self.pre_process(parser)

		if vals[0].vtype[0] == 'sdp' :# and vals[1].val[0] == 'sdp' :
			rv = sdp.bundle([ vals[0].val[0], vals[1].val[0] ])
			return Value(('val', rv), ('vtype', 'sdp'))

		if vals[0].vtype[0] == 'num'  :
			rv = vals[0].val[0] + vals[1].val[0]
			return Value(('val', rv), ('vtype', 'num'))


class Contain(BB):

	def process(self, parser):
		vals = self.pre_process(parser)

		if vals[0].vtype[0] == 'sdp' :
			rv = sdp.contain(vals[0].val[0], vals[1].val[0])
			return Value(('val', rv), ('vtype', 'bool'))


class BundleList(BB):

	def process(self, parser):
		vals = self.pre_process(parser)
		blst = []
		for v in vals : #list of bit-vars
			blst.append(v.val[0])
		rv = sdp.bundle(blst)
		return Value(('val', rv), ('vtype', 'sdp'))



class Complement(BB): pass

class Expr(BiNode): pass

class Assignment(BiNode):

	mem = None

	def process(self, parser):
		val = self.children[1].process(parser)
		self.mem.add(self.Variable[0].name, val.val[0] )
		return Value(('val', True), ('vtype', 'bool') )

class Compare(BB):

	def process(self, parser):
		vals = self.pre_process(parser)

		if vals[0].vtype[0] == 'sdp' and vals[2].vtype[0] == 'sdp' :
			rv = sdp.dist(vals[0].val[0], vals[2].val[0]) == 0
			if vals[1] == '!=' : rv = not rv #reverse
			return Value(('val', rv), ('vtype', 'bool'))

		if vals[0].vtype[0] == 'num' and vals[2].vtype[0] == 'num':
			rv = compare(vals[0].val[0], vals[1], vals[2].val[0])
			return Value(('val', rv), ('vtype', 'bool'))

		if vals[0].vtype[0] == 'string' and vals[2].vtype[0] == 'string':
			rv = compare(vals[0].val[0], vals[1], vals[2].val[0])
			return Value(('val', rv), ('vtype', 'bool'))

		raise Exception("Incompatible types : %s" % self)

class OK(BiNode):

	def __init__(self, lst):
		super(self.__class__, self).__init__(lst)
		log.debug(lst)

	def process(self, parser):
		rv = self.children[0].process(parser)

		string = '' #is there a description
		if len(self.children) > 1 : string = ": " + self.children[1]

		desc1, op, desc2 = '...', '', '...'

		if hasattr(self,  'Contain') :
			obj = self.Contain[0]
			desc1, op, desc2 = '...', 'in', '...'
			if isinstance(obj[0], Variable) : desc1 = obj[0][0]
			if isinstance(obj[1], Variable) : desc2 = obj[1][0]
			if isinstance(obj[0], Number) : desc1 = obj[0][0]
			if isinstance(obj[1], Number) : desc2 = obj[1][0]

		if hasattr(self,  'Compare') :
			obj = self.Compare[0]
			desc1, op, desc2 = '...', obj[1], '...'
			if isinstance(obj[0], Variable) : desc1 = obj[0][0]
			if isinstance(obj[2], Variable) : desc2 = obj[2][0]
			if isinstance(obj[0], Number) : desc1 = obj[0][0]
			if isinstance(obj[2], Number) : desc2 = obj[2][0]

		if rv.val[0] is True : print "?ok:",
		else: print "?nok:",
		print " %s %s %s %s" % (desc1, op, desc2, string)
		return rv

class Say(BiNode):
	def process(self, parser):
		return Value(('val',True),('vtype','bool'))

class Value(BiNode):
	@property
	def value(self): return self.val[0]

	def process(self, parser) :
		log.debug("final: %s" % self)
		return self

class Number(BiNode):
	def process(self, parser) :
		return Value(('val', float(self.children[0])), ('vtype', 'num'))

class String(BiNode):
	def __init__(self, lst):
		super(self.__class__, self).__init__(lst[1:-1])  #strip the quotes


	def process(self, parser) :
		return Value(('val', self.children[0]), ('vtype', 'string'))

class Distance(BB):
	def process(self, parser) :
		vals = self.pre_process(parser)
		return Value( ('val', sdp.dist(vals[0].val[0], vals[1].val[0])), ('vtype', 'num') )

class Bulk(BiNode):
	mem = None
	def process(self, parser) :
		for i in xrange(int(self.Number[0][0]), int(self.Number[1][0])) :
			self.mem.add( self.Variable[0].name + str(i) )
		return true()

class BestMatch(BB):
	cup = None
	def process(self, parser) :
		vals = self.pre_process(parser)
		return Value( ('val', self.cup.best_match(vals[0].val[0])), ('vtype', 'string') )

class PermBind(BB):

	def process(self, parser):
		vals = self.pre_process(parser)
		rv = None
		if vals[0].vtype[0] == 'sdp' :
			a = vals[0].val[0]; b = vals[2].val[0]
			op = vals[1]
			#binding OR probing
			fun = sdp.pbind
			if op.find('<') != -1 : fun = sdp.pprobe

			io = op.strip('><')
			num = None if io == '*' else int(io)
			#if num then roll() else permute()
			if num : rv = fun(a,b,num)
			else : rv = fun(a,b,parser.pmx)

		return Value(('val', rv), ('vtype', 'sdp'))



#=========================================================================================

class BiExpr(object):

	def __init__(self,items=30,nbits=100, log_level=log.INFO, az=True):

		log.root.setLevel(log_level)

		self.lex = lex(items=items,nbits=nbits)
		if az :
			self.lex.nf()
			self.lex.az() #add_items(list(string.lowercase))
		self.grammar = None
		self.rv = None #last return value
		self.expr = None #last expression
		self.pmx = sdp.pmx() #permutation matrix for Permutation-bind
		self.build_grammar()

		#The only plece to reference the Memory is as Class variable
		Variable.mem = self.lex
		Assignment.mem = self.lex
		Bulk.mem = self.lex
		BestMatch.cup = self.lex

	def build_grammar(self):
		spaces = Token('[ \t]+')[:]
		#definition of tokens
#			num = Token('[\+\-]?[0-9]+') >> Number
		num = Token(Real()) > Number

		comma = Token(',')
		dcol = Token(':')
		plus = Token('\+')
		minus = Token('\-')
		contain = Token('in')
		left_bracket = Token('\(')
		right_bracket = Token('\)')
		mult = Token('\*')

		assign_equal = Token('=')
		bit_var = Token('@[@a-zA-Z0-9_!\?]+') > Variable

		string = Token('"[^"]+"') > String
		say = Token('say:')
		hd = Token('hd:')
		ok = Token('ok:')
		bulk = Token('bulk:')
		bm = Token('bm:')
		bundle = Token('bl:')
		tk_roll = Token('roll:')
		tk_perm = Token('perm:')
		nl = Token("\n")
		op_perm = Token("[\*0-9]+>")
		op_iperm = Token("<[\*0-9]+")

#		word = Token('[a-zA-Z_]+')

		with Separator(~spaces):
			cmp_ops = Token('==') | Token('>') | Token('<') | Token('>=') | Token('<=') | Token('!=')
	#		fun_params = (string, bit_var | num)[:,~comma]
	#		sayit = ~say & fun_params > Say
			bulky = ~bulk & bit_var & ~comma & num & ~comma & num > Bulk
			group2, expr = Delayed(), Delayed()

			hdist = ~hd & expr & ~comma & expr > Distance
			best_match = ~bm & expr > BestMatch
			bundle_list = ~bundle & bit_var[1:] > BundleList
			funs = hdist | best_match | bundle_list

			parens = ~left_bracket & expr & ~right_bracket
			group1 = funs | parens | bit_var | num | string
			into = group1 & ~contain & group2 > Contain
			expr_perm = group1 & (op_perm | op_iperm) & group2 > PermBind
			mul = group1 & ~mult & group2 > Bind
			group2 += into | mul | expr_perm | group1
			add = group2 & ~plus & expr > Bundle
			substract = group2 & ~minus & expr > Complement
			expr += add | substract | group2

			assignment = bit_var & ~assign_equal & expr > Assignment

			comparison = expr & cmp_ops & expr > Compare

			ok = ~ok & (comparison | into) & string[:] > OK

#				line = ~spaces & ( ok | bulky | comparison | assignment | expr ) & ~spaces
			line = LineStart() & ( ok | bulky | comparison | assignment | expr ) & LineEnd()
			self.grammar = line[:]
			self.grammar.config.lines()

	def parse(self,txt):
		return self.grammar.parse(txt)

	def process(self, asts):
		rv = []
		if len(asts) == 0 : raise Exception('Nothing to parse')
		for ast in asts :
			log.debug("=============================")

			log.debug(ast)

			new_ast = ast.process(self)
			log.debug("===-- return ast =====")
			log.debug(new_ast)
			rv.append(new_ast)
			log.debug("-----------------------------")

		return rv

	def run(self, txt):
		self.expr = txt
		self.rv = self.process( self.parse(txt.strip()) )
		return self.rv

	@property
	def v(self): print self.rv[0]




