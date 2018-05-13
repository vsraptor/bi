import numpy as np
import math
from encoder import Encoder
from bmap1D import BMap1D
from year_encoder import *
from month_encoder import *
from day_encoder import *

class DateEncoder(Encoder):

	def __init__(self, separator="-", format="ymd"):
		self.sep = separator
		self.format = format
		self.ye = YearEncoder()
		self.me = MonthEncoder()
		self.de = DayEncoder()

	@property
	def info(self):
		s = "> Date encoder -----\n"
		print s
		self.ye.info
		self.me.info
		self.de.info

	def encode(self, value) :
		values = value.split(self.sep)
		res = []
		for i, fmt in enumerate(self.format) :
			if fmt == 'y' : tmp = self.ye.encode(int(values[i]))
			if fmt == 'm' : tmp = self.me.encode(values[i])
			if fmt == 'd' : tmp = self.de.encode(int(values[i]))
			res.append(tmp)
		return res

	def decode(self, value) : raise NotImplementedError

