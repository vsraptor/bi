from __future__ import print_function
from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from bi_expr import *

"""
	ipython extention, so we can do simple bi-expressions in the console.
	Very good for quick tests and examples.

	: %load_ext bi_ip_ext
	: %do @a * @b
	@a * @b
	Value
	+- val 1001111011111101100011111000111001000010101111100010011100000010001101010010100001101010010010000001...
	`- vtype 'sdp'

"""

@magics_class
class BiMagics(Magics):

	def __init__(self, shell):
		super(BiMagics, self).__init__(shell)
		self.bi = BiExpr(nbits=10000)

	@line_magic
	def do(self, line):
		print(line)
		rv = self.bi.run(str(line))
		print(rv[0])
		return rv[0]



def load_ipython_extension(ipython):
	magics = BiMagics(ipython)
	bi = magics.bi
	ipython.register_magics(magics)
	ipython.push(('bi',))
