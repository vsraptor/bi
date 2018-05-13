#!/usr/bin/env python
import re
import logging as log

import imports
imports.import_lib()


"""

	Testing Integration Part2.
	Need ConvD model generated.


"""

from kdb import *
from bi_engine import *
from bi_parser import *
from dyn_atoms import *

from matplotlib import pyplot as plt
import keras
from keras.models import model_from_json

log.root.setLevel(log.INFO)

class Integrate:

	def __init__(self, cupi=True) :
		self.kdb = None
		#use SDPI to mimic integer atoms i.e. virtual SDP
		if cupi :
			log.info('Using <ints> .....')
			self.ints = CUPInteger(vmax=100, width=sdp.nbits/2)
			self.kdb = KDB(items=50, cups=[self.ints])
		else : self.kdb = KDB(items=50) # any digit will get its own entry in .atoms lex

		self.parser = BiParser(kdb=self.kdb, write2db=True)
		#parsed rule-clauses and facts are stored in kdb
		self.parser.parse('./sum.pl')

		self.eng = BiEngine(self.kdb)
		self.load_nn_model()
		self.load_mnist()

	def load_mnist(self, dset='test'):
		log.info("loading MNIST ...")
		self.mnist = np.load(os.path.expanduser('~/.keras/datasets/mnist.npz'))
		self.labels = self.mnist['y_' + dset]
		self.imgs = self.mnist['x_' + dset]

	def load_nn_model(self):
		log.info("loading MNIST model and weights ...")
		json_file = open('mnist_model.json', 'r')
		model_json = json_file.read()
		json_file.close()
		self.model = model_from_json(model_json)
		# load weights into new model
		self.model.load_weights("mnist_model.h5")

	#given DIGIT return image that represent this digit
	def digit2img(self, digit):
		d = np.where(self.labels == digit)[0]
		img_ix = np.random.choice(d)
		return self.imgs[img_ix, :,:] , img_ix

	#show the digit-image, passed as numpy array
	def imshow(self, img):
		plt.imshow(img, cmap='Greys', interpolation='nearest', aspect='auto')
		plt.tight_layout()
		plt.show()

	#given digit-image predict which digit it is, using the trained model
	def predict(self, img) :
		return self.model.predict_classes(img.reshape((1, 28,28, 1)))[0]

	#do a Bi query like :  sum(5,7,Sum)
	def sum(self, val1, val2) :
		mgu = self.eng.query('sum', [ str(val1), str(val2), 'Sum' ])
		return mgu #looks like { 'Sum' : 12 }


	def rand_bi_sums(self, cnt=10) :
		stats = {'ok' : 0 , 'fail' : 0 }

		for _ in xrange(15) :
		 	v1, v2 = np.random.randint(0,9,2)
			ok = v1 + v2
			s = it.sum(v1 , v2)
			print " %s + %s = %s" % (v1, v2, s['Sum'])
			if ok == int(s['Sum']) : stats['ok'] += 1
			else : stats['fail'] += 1

		return stats


	#given two digits, do the whole process :
	#   - convert digit --> image
	#   - recognize the image as digit
	#   - sum the digits using Bi
	#        digits are recognized as atoms
	def calc(self, v1, v2) :
		log.info("calc> v1:%s, v2:%s" % (v1, v2))
		log.info("first pick image that represent the values (randomly)")
		img1, _ = self.digit2img(v1)
		img2, _ = self.digit2img(v2)
		log.info('second: pass trough ConvNN')
		d1 = self.predict(img1)
		d2 = self.predict(img2)
		log.info("predicted> d1:%s, d2:%s" % (d1, d2))
		log.info('... now sum them using Bi lang')
		mgu = self.sum(d1,d2)
		log.info("\n\tresult> %s + %s = %s" % (d1,d2,mgu['Sum']))
		#print self.kdb.atoms


def test():
	it = Integrate()
	v1, v2 = np.random.randint(0,9,2)
	it.calc(v1, v2)
	#print it.rand_bi_sums()

#import sys
#if len(sys.argv) > 1 : test()





