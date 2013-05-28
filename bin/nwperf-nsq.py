#!/usr/bin/env python
# -*- coding: latin-1 -*-
import sys
from nwperf import nnslib

options = {	"addService": [3,5],
		"removeService": [1,1],
		"replaceService": [3,3],
		"getService": [1,1],
		"describeService": [1,1],
		"listServices": [0,0],
		"addDataType": [4,4],
		"listDataTypes": [0,0],
		"removeDataType": [1,1],
		"getDataType": [1,1]}

def usage(msg = None):
	if msg != None:
		print msg
		print
	print "Usage: %s serverUrl <NSCommand> " % sys.argv[0]
	print "\t<NSCommand> is of the following format:"
	print "\t\taddService service location timeout [socketType dataType]"
	print "\t\treplaceService service location timeout"
	print "\t\tremoveService service"
	print "\t\tgetService service"
	print "\t\tdescribeService service"
	print "\t\tlistServices"
	print "\t\taddDataType dataType format requiredFields optionalFields"
	print "\t\tlistDataTypes"
	print "\t\tremoveDataType dataType"
	print "\t\tgetDataType dataType"
	sys.exit()

def main():
	try:
		server = sys.argv[1]
		if ":" not in server:
			server = "tcp://%s:6967" % server
	except:
		usage()
	ns = nnslib.NameServer(server)
	#try:
	if sys.argv[2] not in options.keys():
		usage("Unknown service: %s" % sys.argv[2])
	if len(sys.argv) - 3 < options[sys.argv[2]][0] or  len(sys.argv) - 3 > options[sys.argv[2]][1]:
		usage("Wrong parameter count for service %s" % sys.argv[2])
	try:
		ret = ns.__getattribute__(sys.argv[2])(*sys.argv[3:])
	except nnslib.NameServerException, e:
		print "Server Error:",  e
		sys.exit()
	try:
		for i in ret:
			if type(i) == type(""):
				print i
			else:
				print "\t".join([str(j) for j in i])
	except TypeError, e:
		print "TypeError", e
		pass
	#except:
	#	print "d"
	#	usage()

if __name__ == "__main__":
	main()
