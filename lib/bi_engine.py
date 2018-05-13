import re
import logging as log
log.root.setLevel(log.INFO)

from kdb import *
from bi_utils import *
from collections import deque
__VERSION__ = '0.1'

class BiEngine :

	#descibes from which direction we enter the current sub-goal
	FORWARD = 0
	BACKWARD = 1

	CP_SEARCH_POS = 0
	CP_MGU = 1

	def __init__(self, kdb):
		self.kdb = kdb
		self.fun_slot = self.kdb.syms.g( KDB.fun_sym ) #functor slot
		#choice points stack : holds clause-ix and mgu-frame
		self.stack = deque([])

	#handles atom/variable unification
	def unify_var(self, var, val, mgu):
		if var in mgu :
			return self.unify(mgu[var], val, mgu)
		elif isinstance(val, str) and val in mgu :
			return self.unify(var, mgu[val], mgu)
#		elif self.occurs_check(var, val, mgu) : return False
		else :
			mgu[var] = val ; return mgu

	#the workhorse of the system, accepts the structures formated as list, tuples and/or str
	def unify(self, sym1, sym2, mgu):
		#multichar ! assert len(sym1) == len(sym2), "unify: Missing symbol !"

		if mgu is False : return False
		#when both symbols match
		elif isinstance(sym1, str) and isinstance(sym2, str) and sym1 == sym2 :	return mgu
		#variable cases
		elif isinstance(sym1, str) and is_var(sym1) : return self.unify_var(sym1, sym2, mgu)
		elif isinstance(sym2, str) and is_var(sym2) : return self.unify_var(sym2, sym1, mgu)
		#predicate case : Ex. (fun1, t11, t12, ... ) <=> (fun1, t21, t22, ... )
		elif isinstance(sym1, tuple) and isinstance(sym2, tuple) :
			if len(sym1) == 0 and len(sym2) == 0 : return mgu
			#Functors of structures have to match.
			if isinstance(sym1[0], str) and  isinstance(sym2[0],str) and not ( is_var(sym1[0]) or is_var(sym2[0]) ) and sym1[0] != sym2[0] : return False
			return self.unify(sym1[1:],sym2[1:], self.unify(sym1[0], sym2[0], mgu))
		#list case : Ex. [ s11, s12, ... ] <=> [ s21, s22, ... ]
		elif isinstance(sym1, list) and isinstance(sym2, list) :
			if len(sym1) == 0 and len(sym2) == 0 : return mgu
			return self.unify(sym1[1:],sym2[1:], self.unify(sym1[0], sym2[0], mgu))

		else: return False

	#unwind the variables in the MGU using MGU or VarMAP as a map
	def unlocalize(self, mgu, ctx):
		return { k : mgu.get(v, v) for k, v in ctx.items() if is_var(k) }

	def local_var(self, ctx):#generate local var name
		return '@L' + str(ctx['gc']) + '_' + str(ctx['lc'])

	def is_local_var(self, var_name) : return var_name[:2] == '@L'

	#executing a clause-rule in its own context need localizition of the variables
	# i.e. @1 => L1_1, @3 => L1_3, ...
	def localize(self, syms, ctx):
		local_syms = []; sym = None
		for s in syms :
			if not is_var(s): sym = s
			else :
				if s in ctx : sym = ctx[s]
				else : # create new sym-var, using local-counter & global-counter
					ctx['lc'] += 1
					sym = self.local_var(ctx)
					ctx[s] = sym
			local_syms.append(sym)

		return local_syms

	#extract all the symbols from an SDP and localize them
	def sdp2syms(self, sp, ctx) :
		return self.localize( self.kdb.sdp2syms(sp), ctx)

	#unify two SDP's
	def unify_sdp(self, goal, sdp2, mgu, ctx) :
		syms2 = self.sdp2syms(sdp2, ctx)

		#goal_syms where already generated at .solve()
		if len(ctx['gs']) != len(syms2) : return False #structs cant have diff length
		rv = self.unify(ctx['gs'], syms2, mgu)
		log.debug("  unify> %s %s , %s" % (ctx['gs'], syms2, mgu) )
		return rv

	def match(self, goal_sdp, clause_ix, mgu, ctx) :
		curr_clause = self.kdb.head_sdp(clause_ix)
		rv = self.unify_sdp(goal_sdp, curr_clause, mgu, ctx)
		log.debug( "  match> %s" % (False if rv is False else True) )
		return rv

	def solve_subgoals(self, clause_ix, mgu, ctx, direction) :
		btrack = self.kdb.backtrack(clause_ix) #backtrack-generator
		i = btrack.next()

		#backtrackingly loop over all sub-goals
		while i >= 0 and i < self.kdb.body_count(clause_ix) :
			#get the index of the current subgoal in the "bodys"-DB
			subg_ix =  self.kdb.nth_body_ix(clause_ix, i)

			#depending from which direction we enter the curent subgoal, act accordingly
			if direction == BiEngine.FORWARD :
				pos = 0 #where to start the search in the KDB
				#store choice point info
				self.stack.appendleft([ pos, mgu.copy() ])
			else: #BACKWARD - retry
				pos = self.stack[0][BiEngine.CP_SEARCH_POS]        #start search from next position (where we left off prev) in the DB
				mgu = self.stack[0][BiEngine.CP_MGU       ].copy() #re-populate mgu with a backup copy

			log.debug( "\ncall: direction:%s,i:%s,bix:%s> %s  mgu:%s" % (direction,i,subg_ix, self.kdb.struct_str(subg_ix, mem=self.kdb.bodys), mgu) )
			#try to solve the current sub-goal as a 'standalone goal'
			subg_res = self.solve(self.kdb.body_sdp(subg_ix), mgu, ctx, pos, direction)

			try : #backtracking control

				if subg_res is False : #failed
					direction = BiEngine.BACKWARD #entering from the backdoor
					self.stack.popleft() #retract the last choice point
					i = btrack.send(False) #generator-control
				else : #succeeded
					direction = BiEngine.FORWARD
					mgu = subg_res #update the MGU with the subgoal result
					i = btrack.send(True)

			except StopIteration : #even the first sub-goal failed
				return False

		return mgu #if all body-clauses passed then success


	#implements SLD ... search 'start'-position, direction: enter-direction, ctx: out-in varaibles map
	def solve(self, goal, mgu={}, ctx={}, start_pos=0, direction=FORWARD):

	#	if start_pos > self.kdb.heads.last_ix : return False

		log.debug( "-- %s: solve----------------start:%s>" % (ctx['gc'], start_pos) )

		#prep goal using previous LOCAL variable scope
		if isinstance(goal, list) : goal_syms = goal #already converted to sym-list
		else : goal_syms = self.sdp2syms(goal, ctx=ctx) #unpack the SDP

		# ... new LOCAL var scope : local-counter, global-counter and goal-as-lst-of-syms
		ctx = { 'gc' : self.gc.next(), 'lc' : 0, 'gs' : goal_syms }

		#use indexed DB. list of predicates that match the goal-functor
		functor_ixs = self.kdb.head_pred_lst(goal_syms[0])
		#search through all heads in the DB
		#old: for clause_ix in self.kdb.head_iter(low=start_pos) :

		# SLD : TOP => DOWN processing
		for i, clause_ix in enumerate(functor_ixs[start_pos:]) : #goal_syms[0] is head-functor

			#on FALSE results we need to use unchanged MGU on the next round, so make a copy
			mgu_copy = mgu.copy()

			res = self.match(goal, clause_ix, mgu, ctx)

			#we found a head-match for the current goal
			if res is True or isinstance(res, dict) :
				log.debug( "  cix:%s> %s" % (clause_ix, self.kdb.clause_str(clause_ix)) )

				# .. if this goal is to be retried then start search from the "next" head-clause
				self.stack[0][BiEngine.CP_SEARCH_POS] = start_pos + i + 1 #old: clause_ix + 1

				if self.kdb.is_fact(clause_ix) :
					log.debug( "++ %s <FACT>----: mgu:%s" % (str(ctx['gc']), res) )
					return mgu #success
				else :
					#SLD : LEFT => RIGHT processing
					subg_res = self.solve_subgoals(clause_ix, res, ctx, direction)

					if subg_res is False :
						log.debug( "++ %s <SG-FAIL>----" % (str(ctx['gc'])) )
						return False
			 		else : #unwind localizations
						unwinded_mgu = self.unlocalize(subg_res, subg_res)
						log.debug( "++ %s <SUCCESS>----: mgu:%s" % (str(ctx['gc']), unwinded_mgu) )
						return unwinded_mgu

			#restore the MGU
			else : mgu = mgu_copy.copy()

		#we reached the end of the database
		log.debug( "!!! %s <FAIL>---------------->" )
		return False


	#cleans Local leftover vars from the MGU
	def cleanup(self, mgu):
		return { k : mgu[k] for k in mgu.keys() if not self.is_local_var(k) }

#		new_mgu = {}
#		for k in mgu.keys() :#!fixme
#			if not self.is_local_var(k) : new_mgu[k] = mgu[k]
#		return new_mgu

	def query(self, fun, terms):

		goal = [fun] + terms

		#create goal SDP
#		struct = {'fun': fun, 'terms' : terms }
#		goal_sdp = self.kdb.struct2sdp(struct, counter(), preserve_vars=True, var_kind='G')

		#Localization preparation
		search_pos = 0
		self.gc = counter(low=0, high=100) #SLD levels
		mgu = {}; ctx = { 'gc': self.gc.next(), 'lc': 0 }
		#choice points
		self.stack = deque([[0, mgu.copy()]])

		log.debug( "goal:> %s mgu:%s\n" % (goal, mgu) )
		log.debug( "===================[ %s ]=====================" % search_pos )

		res = self.solve( goal, mgu, ctx, start_pos=search_pos, direction=BiEngine.FORWARD )
		res_mgu = False
		if res is not False :
			res_mgu = self.cleanup(res)
#			res_mgu = self.unlocalize(res, ctx)

		return res_mgu


	def run(self, fun, terms) :

		mgu = self.query(fun, terms)

		log.info("RESULT> %s" % (mgu))

		return mgu