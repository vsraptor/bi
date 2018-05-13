from lark import Lark, Transformer
from bi_utils import *
__VERSION__ = '0.1'


class BiTransformer(Transformer):

	def __init__(self, kdb=None, write2db=False, collect=False) :
		super(self.__class__,self).__init__()
		self.kdb = kdb
		self.write2db = write2db
		self.uid = counter
		self.collect = collect
		self.ccls = [] #collected clauses

	#generate predicate|struct in format suitable for adding to KDB
	def gen(self, lst) :
		rv = None
		if len(lst) == 1 :
			#in case other rule already generated the fun-struct
			if isinstance(lst[0], dict) : return lst[0]
			else : rv = { 'fun' : lst[0] }
		else :
			rv = { 'fun' :  lst[0].children[0], 'terms': lst[1].children }
		return rv

	def int(self, (s,)) : return str(s)
	def atom(self, (s,)) : return str(s)
	def var(self, (s,)) : return str(s)
	def term(self, (s,)) : return str(s)

	def clause(self, items) :
		head = items[0].children[0]
		body = None
		if len(items) > 1 :
			body = items[1].children
	#	print '  %s :- %s' % (head,body)

		#collect rule-clauses for later processing
		if self.collect : self.ccls.append([head,body])
		if not self.write2db or self.kdb is None : return items
		# add to the knowledge base if specified
		self.kdb.add_clause(head, body)

	def struct(self, items) : return self.gen(items)
	def predicate(self, items) : return self.gen(items)
	def assignment(self, items) : return { 'fun' : '=' , 'terms' : items }

	def expr(self, items) :
#		print 'expr> ', items
		return { 'fun' : 'is', 'terms' : [items[0]] + items[1].children }


class BiParser:

	def __init__(self, kdb=None, write2db=False, collect=False):
		self.parser = Lark(self.grammar())
		self.trans = BiTransformer(kdb=kdb, write2db=write2db, collect=collect)

	def parse(self, string) :
		if string.endswith('.pl') :
			with open(string,'r') as f : tmp = f.read()
			ast = self.parser.parse(tmp)
		else :
			ast = self.parser.parse(string)
		return self.trans.transform(ast)

	#collect parsed clauses
	def parse_query(self, line):
		self.trans.collect = True
		self.trans.ccls = []
		rv = self.parse(line)
		return self.trans.ccls

	#create SDP out of bi-lang query
	def query2sdp(self, query):
		assert self.trans.kdb, "we need KDB to create SDP out of dict"
		predicates = []
		clauses = self.parse_query(query)
		for c in clauses :
			for b in c[1] :
				tmp = { 'fun': b } if isinstance(b,str) else b
				predicates.append( self.trans.kdb.struct2sdp(tmp, counter()) )
		return predicates

	def grammar(self):
		grammar = """
		?start : _clause_list

		int  : /[0-9]+/
		atom : /[a-z][0-9a-zA-z_!?]*/
		var  : /[A-Z][0-9a-zA-z_]*/
		functor : atom

		_clause_list : clause+
		head : predicate
		body : _predicates "."
		fact : predicate "."
		clause : fact | head ":-" body

		predicate : atom | functor "(" terms ")" | assignment | expr
		_predicates : predicate ("," predicate)*
		?term : int | atom | var | struct
		terms : term ("," term)*
		struct : functor "(" terms ")"

		?assignment : var "=" term

		?var_int : var | int
		expr : var "is" sum
		?sum : var_int "+" var_int

		%import common.WS
  		%ignore WS
		"""
		return grammar



#!!!!! when hierachical structs are avail
expr = """
		?expr : var "is" sum
		?sum : product
			| sum "+" product
			| sum "-" product

		?product : var_int
			| product "*" var_int
			| product "/" var_int

		?var_int : int
			| "-" int
			| var
			| "(" sum ")"
"""

