#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle “BSD-style” open source license;
# the full text of that license is available in the COPYING file in the root of the repository
import sys
try:
	import cStringIO as stringIO
except ImportError:
	import stringIO
import socket
import time
import xml.sax
import zmq
import os
import atexit
import optparse
import glob
import signal
import traceback
from nwperf import nnslib
import multiprocessing
import Queue
try:
	HIGHWATER=zmq.HWM
except AttributeError:
	HIGHWATER=zmq.SNDHWM

fdlogfile = None
mypidfile = None

class GangliaParser(xml.sax.handler.ContentHandler):
	def __init__(self):
		self.cluster = ""
		self.time = ""
		self.host = ""
		self.points = []

	def startElement(self, name, attrs):
		if name == "METRIC" and attrs["TYPE"] != "string":
			point = {	"host":str(self.host),
					"time":str(self.time),
					"pointname":str(attrs["NAME"]),
					"val":str(attrs["VAL"]),
					"unit":str(attrs["UNITS"])}
			self.points.append(point)
		elif name == "HOST":
			self.host = attrs["NAME"]
		elif name == "CLUSTER":
			self.cluster = attrs["NAME"]
			self.time = attrs["LOCALTIME"]

	def startDocument(self):
		self.points = []

class PointPublisher(object):
	def __init__(self, ns, prefix, ip = None):
		self.ns = nnslib.NameServer(ns)
		self.prefix = prefix
		self.ip = ip
		self.streams = {}
		self.publishTimeout = 600

	def publishPoint(self, point):
		streams = (	"%s.%s" % (self.prefix, point["pointname"]),
				"%s.%s.multipart" % (self.prefix, point["pointname"]),
				"%s.allpoints" % (self.prefix),
				"%s.allpoints.multipart" % (self.prefix))
		streams = [str(i) for i in streams]
		for stream in streams:
			if stream not in self.streams:
				socket = zmq.Context().socket(zmq.PUB)
				socket.setsockopt(HIGHWATER, 15000)
				port = socket.bind_to_random_port("tcp://%s" % self.ip)
				self.streams[stream] = socket
				if "multipart" in stream:
					try:
						self.ns.publishService(stream, "tcp://%s:%s" % (self.ip, port), self.publishTimeout, "pub/sub", "ZmqMultipartPoint")
					except nnslib.NameServerException, e:
						if str(e) == "ZmqMultipartPoint is an unknown data type":
							self.ns.addDataType("ZmqMultipartPoint", "ZmqMultipart", "host,time,pointname,val,unit", "")
						else:
							raise
				else:
					try:
						self.ns.publishService(stream, "tcp://%s:%s" % (self.ip, port), self.publishTimeout, "pub/sub", "Point")
					except nnslib.NameServerException, e:
						if str(e) == "Point is an unknown data type":
							self.ns.addDataType("Point", "JSON", "host,time,pointname,val,unit", "")
						else:
							raise
		jsonPoint = '{"host": "%s", "unit": "%s", "val": "%s", "pointname": "%s", "time": "%s"}' % (point["host"], point["unit"], point["val"], point["pointname"], point["time"])
		multipartPoint = (	"ZmqMultipartPoint",
					"host", point["host"],
					"time", point["time"],
					"pointname", point["pointname"],
					"val", point["val"],
					"unit", point["unit"])
		for stream in streams:
			if "multipart" in stream:
				self.streams[stream].send_multipart(multipartPoint)
			else:
				self.streams[stream].send_multipart(["Point", jsonPoint])

	def updateNameServer(self):
		self.ns.updateServices()

class GangliaParserProcess(multiprocessing.Process):
	def __init__(self, host, port, queue):
		self.socket = socket
		self.host = host
		self.port = port
		self.queue = queue
		super(GangliaParserProcess, self).__init__()
		self.daemon = True
		
	
	def run(self):
		parser = xml.sax.make_parser()
		gparse = GangliaParser()
		parser.setContentHandler(gparse)

		lastCount = 0
		lastTime = time.time()
		while 1:
			try:
				while lastTime + 60 - time.time() < 0:
					lastTime += 60
				time.sleep(lastTime + 60 - time.time())
				parser.parse(stringIO.StringIO(self.retrieveGanglia()))
				self.queue.put(gparse.points)
				print len(gparse.points)
			except Exception, e:
				print traceback.print_exception(type(e), e, sys.exc_info()[2])

	def retrieveGanglia(self):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((self.host, self.port))
		data = sock.recv(1024)
		res = data
		while data != "":
			data = sock.recv(1024)
			res += data
		return res

def delpid():
	global fdlogfile, mypidfile
	print 'in delpid'
	if mypidfile != None:
		os.remove(mypidfile)
	if fdlogfile != None:
		fdlogfile.flush()

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

def main():
	myip = socket.gethostbyname(socket.gethostname())
	optparser = optparse.OptionParser()
	optparser.add_option("-n", "--nodaemon", dest="nodaemon", action="store_true", help="if true, will not daemonize.  this also disables the logfile.  default: False", default=False)
	optparser.add_option("-p", "--pidfile", dest="pidfile", type="string", help="pidfile to use. default: /var/run/ganglia-zmq.pid", default="/var/run/ganglia-zmq.pid")
	optparser.add_option("-l", "--logfile", dest="logfile", type="string", help="logfile to use. default: /var/log/ganglia-zmq.log", default="/var/log/ganglia-zmq.log")
	optparser.add_option("-x", "--prefix", dest="prefix", type="string", help="prefix to prepend to stream types", default=None)
	optparser.add_option("-i", "--ip", dest="ip", type="string", help="ip address to bind to. default: %s" % myip, default=myip)
	(options, args) = optparser.parse_args()

	if options.nodaemon == False:
		daemonize()
		createLogfile(options.logfile)

	# Write PID file
	if options.pidfile != None:
		mypidfile = options.pidfile
		atexit.register(delpid)
		pidfile = file(options.pidfile, 'w+')
		pidfile.write(str(os.getpid()))
		pidfile.close()

	q = multiprocessing.Queue()
	publisher = PointPublisher(args[-1], options.prefix, options.ip)
	sources = [(i.split(":")[0], int(i.split(":")[1])) for i in args[:-1]]
	processes = [GangliaParserProcess(i[0], i[1], q) for i in sources]
	for process in processes:
		process.start()

	def joinProcesses(num=None, frame=None):
		for process in processes:
			process.terminate()
		sys.exit()
	atexit.register(joinProcesses)
	signal.signal(signal.SIGTERM, joinProcesses)
	
	while 1:
		try:
			points = q.get(True, 1)
			for point in points:
				publisher.publishPoint(point)
		except Queue.Empty:
			publisher.updateNameServer()

	joinProcesses()
if __name__ == "__main__":
	main()
