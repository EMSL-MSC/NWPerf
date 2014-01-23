#!/bin/env python
# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle "BSD-style" open source license;
# the full text of that license is available in the COPYING file in the root of the repository
import zmq
import pickle
import time
import optparse
import os
import atexit
import sys
import traceback

mypidfile = None

class ServiceError(Exception):
	pass

class Services(object):
	def __init__(self, statefile=None):
		self.statefile = statefile
		self.services = {}
		self.dataTypes = {}
		try:
			self.__dict__ = pickle.load(open(statefile,"r")).__dict__
		except Exception, e:
			pass

	def addService(self, service, location, timeout, socketType=None, dataType=None):
		if dataType != None and dataType not in self.dataTypes:
			raise ServiceError("%s is an unknown data type" % dataType)

		timeout = int(timeout)
		try:
			self.services[service]["locations"][location] = time.time()+timeout
		except KeyError:
			self.services[service] = {"locations": {location:time.time()+timeout}}
		if "meta" not in self.services[service]:
			self.services[service]["meta"] = {}
		if (socketType == None and "socketType" not in self.services[service]["meta"]) or socketType != None:
			self.services[service]["meta"]["socketType"] = socketType
		else:
			self.services[service]["meta"]["socketType"] = ""
		if (dataType == None and "dataType" not in self.services[service]["meta"]) or dataType != None:
			self.services[service]["meta"]["dataType"] = dataType
		else:
			self.services[service]["meta"]["dataType"] = ""

	def replaceService(self, service, location, timeout, socketType=None, dataType=None):
		self.removeService(service)
		self.addService(service, location, timeout, socketType, dataType)

	def getService(self, service):
		try:
			self.expireService(service)
			return list(self.services[service]["locations"].iteritems())
		except KeyError:
			return None

	def removeService(self, service, location=None):
		if location != None:
			del self.services[service]["locations"][location]
			if len(self.services[service]["locations"]) == 0:
				del self.services[service]
		else:
			del self.services[service]

	def listServices(self):
		for i in self.services.keys():
			self.expireService(i)
		return self.services.keys()

	def describeService(self, service):
		try:
			return (self.services[service]["meta"]["socketType"], self.services[service]["meta"]["dataType"])
		except KeyError:
			return None

	def addDataType(self, dataType, dataFormat, requiredFields, optionalFields):
		self.dataTypes[dataType] = (dataFormat, requiredFields, optionalFields)

	def listDataTypes(self):
		return self.dataTypes.keys()

	def getDataType(self, dataType):
		return self.dataTypes[dataType]

	def removeDataType(self, dataType):
		del self.dataTypes[dataType]

	def saveState(self):
		try:
			pickle.dump(self, open(self.statefile,"w"))
		except:
			pass

	def expireService(self, service):
		now = time.time()
		self.services[service]["locations"] = dict([(k,v) for (k,v) in self.services[service]["locations"].iteritems() if v > now])
		if self.services[service]["locations"] == {}:
			del self.services[service]

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
	global mypidfile
	os.remove(mypidfile)

def main():
	global mypidfile
	parser = optparse.OptionParser()
	parser.add_option(	"-l", "--logfile", dest="logfile", type="string", help="logfile to use. default: /var/log/moab-zmq.log", default="/var/log/nwperf.log")
	parser.add_option(	"-s", "--statefile", dest="statefile", type="string",
				help="statefile to maintain service listings between sessions. default: /var/lib/nwperf-ns/nwperf-ns", default="/var/lib/nwperf-ns/nwperf-ns")
	parser.add_option(	"-p", "--pidfile", dest="pidfile", type="string",
				help="pidfile to use. default: /var/run/nwperf-ns.pid", default="/var/run/nwperf-ns.pid")
	parser.add_option("-n", "--nodaemon", dest="nodaemon", action="store_true", help="if flag is set, then this script will not daemonize.  this also disables the logfile.  default: False", default=False)

	(options, args) = parser.parse_args()
	mypidfile = options.pidfile

	if options.nodaemon == False:
		daemonize()
		createLogfile(options.logfile)

	# Write PID file
	if options.pidfile != None:
		atexit.register(delpid)
		pidfile = file(options.pidfile, 'w+')
		pidfile.write(str(os.getpid()))
		pidfile.close()

	services = Services(options.statefile)
	if options.nodaemon:
		print "Initial State: %s" % services.services
		print "Initial Data Types: %s" % services.dataTypes
	
	ctx = zmq.Context()
	sock = ctx.socket(zmq.REP)
	sock.bind("tcp://*:6967")

	while True:
		msg = sock.recv_multipart()
		if options.nodaemon:
			print "Request: %s" % msg
		if msg[0] == "1":
			try:
				if msg[1] in ("addService", "replaceService", "removeService", "addDataType", "removeDataType"):
					services.__getattribute__(msg[1])(*msg[2:])
					if options.nodaemon:
						print "Response: OK"
					sock.send("OK")
					services.saveState()
				elif msg[1] in ("listServices", "listDataTypes"):
					try:
						rsp = services.__getattribute__(msg[1])()
						if options.nodaemon:
							print "Response: %s" % rsp
						sock.send_multipart(rsp)
					except IndexError:
						if options.nodaemon:
							print "Response: %s" % (["ERROR", "None Found"])
						sock.send_multipart(["ERROR", "None Found"])
				elif msg[1] in ("describeService", "getDataType"):
					rsp = services.__getattribute__(msg[1])(msg[2])
					if rsp != None:
						print rsp
						if options.nodaemon:
							print "Response: %s" % rsp
						sock.send_multipart(rsp)
					else:
						rsp = ["ERROR", "%s not Found" % {"describeService":"Service", "getDataType":"Data type"}[msg[1]]]
						if options.nodaemon:
							print "Response: %s" % rsp
						sock.send_multipart(rsp)
				elif msg[1] == "getService":
					rsp = services.getService(msg[2])
					if rsp != None:
						now = time.time()
						rsp = sum([[i[0], str(int(i[1]-now))] for i in rsp], [])
						if options.nodaemon:
							print "Response: %s" % rsp
						sock.send_multipart(rsp)
					else:
						if options.nodaemon:
							print "Response: %s" % (["ERROR", "Service not Found"])
						sock.send_multipart(["ERROR", "Service not Found"])
				else:
					if options.nodaemon:
						print "Response: %s" % (["ERROR", "Unknown function call"])
					sock.send_multipart(["ERROR", "Unknown function call"])
			except Exception, e:
				print traceback.print_exception(type(e), e, sys.exc_info()[2])
				if options.nodaemon:
					print "Response: %s" % (["ERROR",str(e)])
				sock.send_multipart(["ERROR", str(e)])
		else:
			if options.nodaemon:
				print "Response: %s" % (["ERROR", "Unknown Version"])
			sock.send_multipart(["ERROR", "Unknown Version"])

if __name__ == "__main__":
	main()
