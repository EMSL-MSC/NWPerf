import collectd
from nwperf import nnslib
import zmq
import time
import threading
import Queue
try:
        HIGHWATER=zmq.HWM
except AttributeError:
        HIGHWATER=zmq.SNDHWM

class Cls:
	pass
self=Cls()
self.nameserver="unknown"
self.cluster="none"
self.ns=None
self.ip="0.0.0.0"
self.publishTimeout=600
self.resettime=0
self.q = Queue.Queue()
self.qthread = None

class PublishThread(threading.Thread):
	def __init__(self,socket,ns,q):
		threading.Thread.__init__(self)
		self.socket=socket	
		self.ns=ns
		self.q = q

	def run(self):
		resettime=time.time()+300
		while True:
			if self.q.empty():
				if time.time()>resettime:
					resettime=time.time()+300
					self.ns.updateServices()
				time.sleep(5)
			dp = self.q.get()
			self.socket.send_multipart(["Point", dp])
			self.q.task_done()

def config(conf):
	global self
	if conf.values[0]=="nwcollectd":
		for i in conf.children:
			if i.key == "NameServer":
				self.nameserver=i.values[0]
			if i.key == "ClusterName":
				self.cluster = i.values[0]
			if i.key == "IP":
				self.ip = i.values[0]
def init():
	global self
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
	

def write(vl, data=None):
	for i in vl.values:
		#	print "%s: %s-%s (%s-%s): %f" % (vl.host,vl.plugin,vl.plugin_instance, vl.type,vl.type_instance, i)
		jsonPoint = '{"host": "%s", "unit": "%s", "val": "%s", "pointname": "%s.%s.%s.%s", "time": "%s"}' % (vl.host, "unk", i, vl.plugin,vl.plugin_instance,vl.type,vl.type_instance,vl.time)
		#print jsonPoint
		self.q.put(jsonPoint)
		

def shutdown():
	self.ns.removeServices()


collectd.register_config(config)
collectd.register_init(init)
collectd.register_write(write)
collectd.register_shutdown(shutdown)
