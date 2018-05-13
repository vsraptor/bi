#!/usr/bin/env python
import imports
imports.import_lib()

from bi_engine import *
from kdb import *

k = KDB()
s = BiEngine(k)

def test(a,b):
	res = s.unify(a,b, {})
	if res or isinstance(res, dict) : print "OK: %s <=> %s : %s" % (str(a),str(b), str(res))
	else : print "FAIL: %s <=> %s : %s" % (str(a),str(b),str(res))

#testing assertion
#!!test('','')
#test('a','')
#test('','a')
#test('a',())
#test(('a'),('a','b'))

test('a','a')
test('X','a')

test(['a'],['a'])
test(['X'],['a'])
test(['a'],['X'])
test(['X'],['X'])
test(['X'],['Z'])

test(['p','a'],['p','a'])
test(['p','X'],['p','a'])
test(['p','X'],['p','X'])
test(['p','X'],['p','Z'])
test(['X','X'],['p','X'])


test(['p','X', 'Y'],['p','Y', 'X'])
test(['p','X', 'Y', 'a'],['p','Y', 'X', 'X'])

print "================= STRUCT cases ==================="

test(['e','X', ('p', 'a')],['e','Y', ('p', 'a')] )
test(['e','X', ('p', 'a')],['e','Y', ('p', 'Z')] )
test(['e','X', ('p', 'a')],['e','Y', ('P', 'Z')] )
test([('p', 'a', 'X')],[('p','Y', 'b')] )
test(['X', 'Y'],[('p', 'a'), 'X'] )
test([('p', 'a')],['X'] )

test([ ('foo', ('bar', 'X'), 'W', ('blah', ('bleh', 'Y')) ) ], [ ('foo','Z', 'Z', ('blah','X')) ] )

print '-----'
test([('p', 'a')],[('p1', 'a')] )
test([('p', 'a')],[('p1', 'X')] )
test(['e','X', ('p1', 'a')],['e','Y', ('p2', 'Z')] )
test(['e','X', ('p1', 'a')],['e','Y', ('p1', 'b')] )
test([('p', 'a', 'X', 'X')],[('p','a', 'a', 'b')] )
test([('p1', 'X', 'X')],[('p1','Y', ('p2','Y'))] ) #!!occurs check


print "================= LIST cases ==================="

test(['e','X', ['e', 'a']],['e','Y', ['e', 'a']] )
test(['e','X', ['a', 'a']],['e','Y', ['a', 'Z']] )
test(['e','X', ['e', 'a']],['e','Y', ['E', 'Z']] )
test(['e','X', ['e1', 'a']],['e','Y', ['e1', 'a']] )

test([['e', 'a']],['X'] )
test(['X'],[['e', 'a']] )

print "================= FAIL cases ==================="

test(['a'],['b'])
test(['p','a'],['p','b'])
test(['X','X'],['p','b'])


