from kdb import *

class Struct:

	def __init__(self, db, functor, terms):
		self.db = db
		self.functor = functor
		self.terms = [ t.name for t in terms ]

	def __pos__(self):
		self.db.kdb.add_clause({'fun': self.functor.name, 'terms' : self.terms})

	def __lshift__(self, body):
		bodys = []
		if not isinstance(body, tuple) : #clause with single elem in the body
			bodys.append({'fun': body.functor.name, 'terms' : body.terms })
		else :
			for b in body :
				tmp = {'fun' : b.functor.name, 'terms' : b.terms }
				bodys.append(tmp)
		self.db.kdb.add_clause({'fun': self.functor.name, 'terms' : self.terms}, bodys)


class Symbol:

	def __init__(self, name, db) :
		self.name = name
		self.db = db

	#actual call to add clause, from inside the decorated function
	def __call__(self, *args):
		return Struct(self.db, self, args)

	def __str__(self) : return self.name

#Decorator for Bi-lang-python functions
class bilight(object):

	def __init__(self, kdb):
		self.kdb = kdb

	#Define all atoms used in decorated function, so that
	# when we call it it does not throw error
	# then execute the function in this safe environment
	def __call__(self, fun):
		try:
			code = fun.func_code
		except:
			raise TypeError, "function or method argument expected"
		#print code.co_names
		#print code.co_varnames
		#print fun.func_globals.keys()
		names = code.co_names
		locally_defined = code.co_varnames
		globally_defined = fun.func_globals.keys()
		defined = locally_defined + tuple(globally_defined)
		undefined = [name for name in names if name not in defined]
		new_globals = fun.func_globals.copy()
		for name in undefined:
			new_globals[name] = Symbol(name, self)
		exec code in new_globals
