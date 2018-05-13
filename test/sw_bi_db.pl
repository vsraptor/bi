female(leia).
male(luke).
male(vader).
male(kylo).
female(padme).
male(han).
male(ruwee).
female(jobal).
female(shmi).

child(luke, vader).
child(leia, vader).
child(leia, padme).
child(kylo, leia).
child(kylo, han).
child(luke, padme).
child(padme, ruwee).
child(padme, jobal).
child(vader, shmi).

son(X,Y) :- child(X,Y), male(X).
daughter(X,Y) :- female(X), child(X,Y).
ds(X,Y) :- daughter(X,Y).
ds(X,Y) :- son(X,Y).

grandchild(X,Z) :- child(X,Y), child(Y,Z).
gc_ds(X,Z) :- ds(X,Y), ds(Y,Z).
gcm(X,Y) :- grandchild(X,Y), male(X).
rgcm(X,Y) :- male(X), grandchild(X,Y).
bgcm(X,Y) :- male(X), grandchild(X,Y), male(X).


