import sys, os
def import_lib() :
	basedir = os.path.abspath(os.path.dirname(__file__))
	for d in ['../lib/encoders', '../lib/cups', '../lib'] :
		libdir = os.path.abspath(os.path.join(basedir, d));
		sys.path.insert(0,libdir)

