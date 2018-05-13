next(0,1).
next(1,2).
next(2,3).
next(3,4).
next(4,5).
next(5,6).
next(6,7).
next(7,8).
next(8,9).
next(9,10).
next(10,11).
next(11,12).
next(12,13).
next(13,14).
next(14,15).
next(15,16).
next(16,17).
next(17,18).
next(18,19).
next(19,20).

prev(A,B) :- next(B,A).
sum(S,0,S).
sum(A,B,S) :- next(A,A1), prev(B,B1), sum(A1,B1,S).
