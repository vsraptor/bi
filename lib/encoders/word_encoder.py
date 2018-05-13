from encoder import Encoder
from category_encoder import *
from bmap1D import BMap1D
import string
import logging as log

#!!! This encoder produces Dense representation i.e. it is not good for use where SDR are needed

class WordEncoder(Encoder):

	cmap = {} # char to bin map
	ce = None # Category encoder

	@classmethod
	def init_cmap(cls, nbits=26):
		log.debug('Building charachter map : %sbit code ...' % nbits)
		if nbits > 26 :
			cls.ce = CategoryEncoder(nbits=nbits,ncats=26)

		for i,c in enumerate(string.ascii_lowercase) :
			if nbits == 5 :
				cls.cmap[c] = BMap1D(format(i+1,'b').zfill(nbits)) #5bits for 26 chars
				continue
			if nbits == 26 : #26 bits for 26 chars
				bmap = BMap1D(nbits)
				bmap[i:] = 1
				cls.cmap[c] = bmap
				continue
			if nbits > 26 :
				cls.cmap[c] = cls.ce.encode(i+1)
				continue

	@property
	def info(self) :
		print "> Word encoder "
		print "nbits : %s" % self.nbits
		self.__class__.info

	def __init__(self, nbits=400,encoder_nbits=26):
		if WordEncoder.cmap == {} : self.__class__.init_cmap(nbits=encoder_nbits)
		self.nbits = nbits
		self.cmap_width = len(self.cmap['a'])

	def encode(self, word) :
		val = BMap1D()
		val.encode(WordEncoder.cmap, word.lower())
		rv = BMap1D(self.nbits)
		length = len(val) if len(val) < self.nbits else self.nbits
		rv[0:length] = val[0:length] #keep correct size
		return rv

	def decode(self, bmap) :
		return str.join('', bmap.decode(WordEncoder.cmap))

	#!fixme : use BMAP2D
	def best_char(self, bmap) :
		best = ""
		minn = self.cmap_width
#		print minn
		for c in self.__class__.cmap.keys() :
			cnt = (self.__class__.cmap[c] ^ bmap).count()
			if cnt < minn :
				minn = cnt
				#zzzzzzzzzzzz
				if cnt == 1 and not bmap[-1] == 1 : best = " "
				else : best = c
		return best

	def one_hot_best_match(self, bmap) :
#		print ">> ", bmap
#		word = " " * int(self.nbits / self.cmap_width)
		word = ""
		for p in xrange(0,self.nbits, self.cmap_width) :
			char_bin = bmap[p : p + self.cmap_width]
			#skip if not full char
			if len(char_bin) < self.cmap_width : continue
#			print p, char_bin
#			print "bc> ", self.best_char(char_bin)
			word += self.best_char(char_bin)
		return word.rstrip()


	def cat_best_match(self, bmap):
		word = ""
		for p in xrange(0,self.nbits, self.cmap_width) :
			char_bin = bmap[p : p + self.cmap_width]
			#skip if not full char
			if len(char_bin) < self.cmap_width : continue
			idx = self.__class__.ce.decode(char_bin)
			char = chr(ord('a') + idx )
		#print idx, char
			word += char # self.__class__.cmap[char]
		return word

