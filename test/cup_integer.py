#!/usr/bin/env python
import re
import logging as log
import seaborn as sns

import os, sys
basedir = os.path.abspath(os.path.dirname(__file__))
libdir = os.path.abspath(os.path.join(basedir, '../lib'));
sys.path.insert(0,libdir)

"""
	Test the capability of CUPInteger to represent integer range.
	Counts false-negative.

	x-axis : range-max
	y-axis : flips/noise

"""

from dyn_atoms import *
from autovivification import *
from matplotlib import pyplot as plt

log.root.setLevel(log.INFO)

def test(test_range, vmin=0, vmax=100, flips=10):
	stats = { 'ok' : 0, 'fail' : 0 }
	ints = CUPInteger(vmin=vmin, vmax=vmax, width=sdp.nbits/2)
	for i in test_range :
		enc = ints.encode_sdp(i)
		sdp.flip_bits(enc,flips)
		bm = ints.best_match(enc)
	#	print "dist: ", (sdp.dist(ints.encode_sdp(i), enc))
		#print " %s <=> %s " % (i,bm)
		if str(i) == bm : stats['ok'] += 1
		else : stats['fail'] += 1
	return stats

def tests(items):
	vmin = 0; all_stats = AutoVivification({})
	np_stats = np.zeros(( len(flippings), len(list(maxes)) ), dtype=int)
	for x, vmax in enumerate(maxes) :
		for y, flips in enumerate(flippings) :
			print "vmax:%s, flips:%s, items:%s" % (vmax, flips, items)
		 	stats = test(np.random.randint(vmin, vmax, items), vmin=vmin, vmax=vmax, flips=flips)
			print stats
			#all_stats[vmax][flips] = stats
			np_stats[x,y] = stats['fail']
	return np_stats


def show(data, x_axis, y_axis):
	sns.set(style="white")
	cmap = seq_col_brew = sns.color_palette("Greys", 16)
	f, ax = plt.subplots(figsize=(10, 10))
	ax = sns.heatmap(np.flipud(data), cmap=cmap, vmax=10000, vmin=0,
		square=True, linewidths=.5, cbar_kws={"shrink": .5}, annot=True, fmt='d',
		xticklabels=x_axis, yticklabels=y_axis[::-1])
	f.tight_layout()

def run() :
	items=100

	rv = tests(items)
	print rv
	np.save('cup-int'+str(items)+'.npy', rv)

flippings = [ 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4200, 4500 ]
maxes = xrange(100,1001,100)
run()

#plt.grid()
#plt.imshow(np.flipud(rv), cmap='Greys', interpolation='nearest', aspect='auto')
#plt.tight_layout()
#plt.show()

#vmin = 0
#vmax = 1000
#test(np.random.randint(vmin,vmax,100000),vmin=vmin, vmax=vmax, flips=300)

#range:100, flip:3000, rand: 200_000
#range:200, flips:2200 rand:
#range:1000, flips:300, rand: 100_000
#print stats