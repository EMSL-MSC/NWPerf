import collectd
# -*- coding: latin-1 -*-
#
from nwperf import nnslib
from nwperf import Settings
import zmq
import time
import threading
import multiprocessing
import Queue
import json
import os
try:
        HIGHWATER=zmq.HWM
except AttributeError:
        HIGHWATER=zmq.SNDHWM


class PublishThread(threading.Thread):
	def __init__(self,socket,ns,q):
		threading.Thread.__init__(self)
		self.socket=socket	
		self.ns=ns
		self.q = q
		self.die = False

	def terminate(self):
		self.die = True

	def run(self):
		resettime=time.time()+300
		while not self.die:
			try:
				dp = self.q.get_nowait()
				self.socket.send_multipart(["Point", dp])
			except Queue.Empty:
				if time.time()>resettime:
					resettime=time.time()+300
					self.ns.updateServices()
				time.sleep(5)


class NWCollectd:
	def __init__(self,typeinfo):
		self.nameserver="unknown"
		self.cluster="none"
		self.ns=None
		self.ip="0.0.0.0"
		self.publishTimeout=600
		self.q = multiprocessing.Queue()
		self.qthread = None
		self.typeinfo = typeinfo
	
		collectd.register_config(self.config)
		collectd.register_init(self.init)
		collectd.register_write(self.write)
		collectd.register_shutdown(self.shutdown)

	def config(self,conf):
		if conf.values[0]=="nwcollectd":
			for i in conf.children:
				if i.key == "NameServer":
					self.nameserver=i.values[0]
				if i.key == "ClusterName":
					self.cluster = i.values[0]
				if i.key == "IP":
					self.ip = i.values[0]

	def init(self):
		self.ns = nnslib.NameServer(self.nameserver)
		self.socket = zmq.Context().socket(zmq.PUB)
		self.socket.setsockopt(HIGHWATER, 15000)
		port = self.socket.bind_to_random_port("tcp://%s" %self.ip)
		try:
			self.ns.publishService(self.cluster+".points", "tcp://%s:%s" % (self.ip, port), self.publishTimeout, "pub/sub", "Point")
			self.resettime = time.time()+300
		except nnslib.NameServerException, e:
			collectd.error("Error",e)
		self.qthread = PublishThread(self.socket,self.ns,self.q)
		self.qthread.setDaemon(True)
		self.qthread.start()
		

	def write(self,vl, data=None):
		for i in vl.values:
			#print "%s: %s-%s (%s-%s): %f" % (vl.host,vl.plugin,vl.plugin_instance, vl.type,vl.type_instance, i)
			try:
				unit=str(self.typeinfo[vl.plugin]['unit'])
			except:
				unit="unknown"
			name= '.'.join(filter(None,[vl.plugin,vl.plugin_instance,vl.type,vl.type_instance]))
			jsonPoint = '{"host": "%s", "unit": "%s", "val": "%s", "pointname": "%s", "time": "%s"}' % (vl.host, unit, i, name,vl.time)
			#print jsonPoint
			self.q.put(jsonPoint)
			

	def shutdown(self):
		self.qthread.terminate()
		self.ns.removeServices()

settings=Settings("/etc/nwperf.conf")
typeinfo=settings["collectdtypes"]

TheOne = NWCollectd(typeinfo)
