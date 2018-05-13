import collections

def slot(i) : return '$' + str(i)
def var_name(hi, kind='')  : return '@' + kind + str(hi)

def is_var(vv) : return isinstance(vv,str) and ( vv[0].isupper() or vv[0] == '@' )
def is_slot(v): return v is None or not v[0] == '$' 


#def sdp2sym(sdp, cup): return cup.bm(sdp)

def counter(low=1, high=20):
	current = low
	while current <= high:
		yield current
		current += 1

def inf_counter(low=1):
	current = low
	while True :
		yield current
		current += 1

def var_counter(head_ix, low=1, high=20):
	current = low; head_ix = str(head_ix)
	while current <= high:
		yield head_ix + '_' + str(current)
		current += 1

def rachet(low=0, high=100):
	current = low; check_point = low
	while current <= high:
		msg = yield current
		if msg == 'check_point' : check_point = current 
		elif msg == 'jump' : current = check_point
		else : current += 1


#returns sequentialy all the elemets of sdp-bind-tuples
def slotting(sdp1, sdp2, cup, low=0, high=20):
	current = low
	while True :
		new1 = cup.bm( cup.g(slot(current)) * sdp1 )
		new2 = cup.bm( cup.g(slot(current)) * sdp2 )
		if current >= high or ( new1 is None or new2 is None ) : return
		yield new1, new2
		current += 1


def merge_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

#specifics: don't flatten strings and dicts
def flatten(lst):
    for el in lst:
        if isinstance(el, list) :# and not isinstance(el, (basestring,dict)):
            for sub in flatten(el): yield sub
        else: yield el


