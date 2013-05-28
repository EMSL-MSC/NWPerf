#!/bin/env python
# -*- coding: latin-1 -*-
#
# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle “BSD-style” open source license;
# the full text of that license is available in the COPYING file in the root of the repository
import zmq
import time
import optparse
import os
import atexit
import sys
import traceback
import nnslib
from operator import itemgetter
import datetime

_parser = None
_options = None

from Settings import *

def isoToEpoch(iso):
    t = datetime.datetime.strptime(iso,'%Y-%m-%dT%H:%M:%S')
    return int(time.mktime(t.timetuple()))

def timeToSeconds(hms):
	if hms[1]=='-': #hack to pull off days, double digit days hose this.. proper parsing would be better
		days=int(hms[0])
		hms=hms[2:]
	else:
		days=0
	t = datetime.timedelta(days=days,hours=int(hms[:2]),minutes=int(hms[3:5]),seconds=int(hms[6:]))
	return int(t.seconds+t.days*86400)

def getJobInfo(jid,cluster,nameserver):
	ns=nnslib.NameServer(nameserver)

	try:
		srv = ns.getService(cluster+".slurm.jobinfo")
		srv.sort(key=itemgetter(1))
		url=srv[-1][0]
		#print srv,url
	except nnslib.NameServerException,msg:
		print "Error:",msg
		return {}

	c = zmq.Context()
	s = c.socket(zmq.REQ)
	s.connect(url)
	s.send_multipart(("jobinfo",str(jid)))
	info=s.recv_json()
	return info

def getJobTimes(info,minutes):
	try:
		s=isoToEpoch(info['Start'])
		e=timeToSeconds(info['Elapsed'])+s
		#it would be nice if we could predict end time here...

		if info['State'] == 'RUNNING':
			e=max(e,s+minutes*60)
		elif info['State'] == 'PENDING':
			e=0
			s=0
		else:
			#print "E:",s,e,minutes
			if minutes>0:
				e=min(e,s+minutes*60)
	
		return s,e
	except Exception,msg:
		print "Error getting times:",msg
		return 0,0	

def daemonize():
	try:
		pid = os.fork()
	except OSError, e:
		raise Exception, "%s [%d]" % (e.strerror, e.errno)

	if (pid == 0): 
		os.setsid()
		try:
			pid = os.fork()
		except OSError, e:
			raise Exception, "%s [%d]" % (e.strerror, e.errno)

		if (pid == 0): 
			os.chdir("/")
			#os.umask(0)
		else:
			os._exit(0)
	else:
		os._exit(0)

	# Close all open file descriptors
	for fd in range(0, 1024):
		try:
			os.close(fd)
		except OSError:
			pass

	os.open(os.devnull, os.O_RDONLY)
	return(0)

def createLogfile(filename):
	if filename != None:
		# Touch the file if it doesn't exist
		if not os.path.isfile(filename):
			open(filename, 'w').close()
		# open our log file for appending
		fdlogfile = os.open(filename, os.O_APPEND|os.O_WRONLY)
		# redirect stderr to the log file opened above
		os.dup2(fdlogfile, 2)

def delpid():
	"""helper function to cleanup the pid file"""
	global _options
	os.remove(_options.pidfile)

def defaultServerOptionParser():
	"""Retrieve a Option parser with default options for a deamonizable Server"""
	global _parser
	prog=os.path.basename(sys.argv[0])
	if prog.endswith(".py"):
		prog=prog[:-3]
	_parser = optparse.OptionParser()
	_parser.add_option(	"-l", "--logfile", dest="logfile", type="string", help="logfile to use. default: /var/log/%s.log"%(prog), default="/var/log/%s.log"%(prog))
	_parser.add_option(	"-p", "--pidfile", dest="pidfile", type="string",
				help="pidfile to use. default: /var/run/%s.pid"%(prog), default="/var/run/%s.pid"%(prog))
	_parser.add_option("-n", "--nodaemon", dest="nodaemon", action="store_true", help="if flag is set, then this script will not daemonize.  this also disables the logfile.  default: False", default=False)
	return _parser

def parseServerOptions():
	"""parses the arguments, and deals with defaults, returning the options, and args as a tuple: replaces parser.parse_args()"""

	(_options, args) = _parser.parse_args()

	#check access of files
	if _options.nodaemon == False and os.access(os.path.dirname(_options.logfile),os.W_OK) == False:
		_parser.error("Logfile directory write access will be denied")
	if os.access(os.path.dirname(_options.pidfile),os.W_OK) == False:
		_parser.error("Pidfile directory write access will be denied")

	if _options.nodaemon == False:
		daemonize()
		createLogfile(_options.logfile)

	# Write PID file
	if _options.pidfile != None:
		def _delpid(file=_options.pidfile):
			os.remove(file)
		atexit.register(_delpid)
		pidfile = file(_options.pidfile, 'w+')
		pidfile.write(str(os.getpid()))
		pidfile.close()

	return _options,args

if __name__ == "__main__":
	import time
	parser = defaultServerOptionParser()
	parser.add_option( "-s", "--sleep", dest="sleeptime", type="int", help="The amount of seconds to sleep before exiting", default=5)
	
	options,args = parseServerOptions()

	time.sleep(options.sleeptime)
	sys.stderr.write("Log Entry\n")

