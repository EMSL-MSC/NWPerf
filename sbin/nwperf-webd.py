#!/usr/bin/env python
# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle "BSD-style" open source license;
# the full text of that license is available in the COPYING file in the root of the repository
import sys
import os
import tarfile
import time
import hostlist
import multiprocessing
import zmq
try:
	import cStringIO as StringIO
except ImportError:
	import StringIO
try:
	import simplejson as json
except ImportError:
	import json
import nwperf
from nwperf import nnslib
from nwperf import MongoJobStore, MongoPointStore

class JobArchiveGenerator(multiprocessing.Process):
	def __init__(self, pointStore, q, jobStore, runOnce = False, extraFields = {}):
		self.pointStore = pointStore
		self.q = q
		self.jobStore = jobStore
		self.runOnce = runOnce
		self.extraFields = extraFields
		super(JobArchiveGenerator, self).__init__()

	def run(self):
		self.jobStore.fork()
		while True:
			job = self.q.get()
			print job
			startTime = int(time.strftime("%s", time.strptime(job["Start"], "%Y-%m-%dT%H:%M:%S")))
			endTime = int(time.strftime("%s", time.strptime(job["End"], "%Y-%m-%dT%H:%M:%S")))
			points = self.pointStore.getPoints(startTime, endTime, job["Nodes"])
			self.jobStore.processJob(job, points, self.extraFields)

class PointStoreProcess(multiprocessing.Process):
	def __init__(self, pointStore, ns, service):
		self.pointStore = pointStore
		self.service = service
		self.ns = ns
		super(PointStoreProcess, self).__init__()
		self.daemon = True

	def run(self):
		ns = nnslib.NameServer(self.ns)
		ctx = zmq.Context()
		count = 0
		sock = ctx.socket(zmq.SUB)
		sock.setsockopt(zmq.SUBSCRIBE, "")
		ns.connectService(sock, self.service)
		poll = zmq.core.poll.Poller()
		poll.register(sock, zmq.POLLIN)
		while True:
			res = poll.poll(1000)
			if res:
				count += 1
				if count > 1000000:
					print "emergency flush", time.ctime()
					count = 0
					self.pointStore.flush()
				(header, payload) = sock.recv_multipart()
				payload = json.loads(payload)
				# As far as I know, slurm only reports the first part of the hostname so we should only
				# store the first entry in the name
				payload["host"] = payload["host"].split(".")[0]
				self.pointStore.savePoint(payload["host"], payload["pointname"], payload["time"], payload["val"])
			else:
				count = 0
				self.pointStore.flush()
				try:
					ns.updateSocket(sock)
				except:
					sock = self.ctx.socket(zmq.SUB)
					sock.setsockopt(zmq.SUBSCRIBE, "")
					ns.connectService(sock, self.service)
					poll = zmq.core.poll.Poller()
					poll.register(sock, zmq.POLLIN)
	
def main():
        parser = nwperf.defaultServerOptionParser()
        parser.add_option(      "-c", "--cluster", action="store", type="string", dest="cluster",
                                help="name of cluster to generate graphs for")
        parser.add_option(      "-S", "--name-server", action="store", type="string", dest="nameserver",
                                help="The ZMQ URL of the nameserver")
        parser.add_option(      "-j", "--job-service", action="store", type="string", dest="jobservice",
                                help="The service name that provides job information")
        parser.add_option(      "-P", "--point-service", action="store", type="string", dest="pointservice",
                                help="The service name that provides point data")

        (options, args) = nwperf.parseServerOptions()

	if not options.nameserver:
		parser.error("No name server specified")

	if not options.pointservice:
		parser.error("No point service specified")

	if not options.jobservice:
		parser.error("No job service specified")

	if not options.cluster:
		parser.error("No cluster specified")

	pointStore = MongoPointStore.MongoPointStore()
	jobStore = MongoJobStore.MongoJobStore()

	ns = nnslib.NameServer(options.nameserver)
	ctx = zmq.Context()
	q = multiprocessing.Queue()
	#if not options.generategraphs:
	children = [JobArchiveGenerator(pointStore, q, jobStore, extraFields={"cluster": options.cluster}) for i in range(8)]
	for child in children:
		child.start()
	psp =  PointStoreProcess(pointStore, options.nameserver, options.pointservice)
	psp.start()

	sock = ctx.socket(zmq.SUB)
	sock.setsockopt(zmq.SUBSCRIBE, "JobEnd")
	ns.connectService(sock, options.jobservice)
	while True:
		poll = zmq.core.poll.Poller()
		poll.register(sock, zmq.POLLIN)
		res = poll.poll(1000)
		if res:
			job = sock.recv_multipart()[1]
			job = json.loads(job)
			job["Nodes"] = hostlist.expand_hostlist(job["NodeList"])
			q.put(job)
		for i in range(len(children)):
			if not children[i].is_alive():
				children[i].join()
				del(children[i])
				newchild = JobArchiveGenerator(pointStore, q, jobStore, extraFields={"cluster": options.cluster})
				newchild.start()
				children.append(newchild)
		try:
			ns.updateSocket(sock)
		except:
			sock.close()
			sock = ctx.socket(zmq.SUB)
			sock.setsockopt(zmq.SUBSCRIBE, "JobEnd")
			ns.connectService(sock, options.jobservice)
			poll.register(sock, zmq.POLLIN)
		if q.qsize() > 0:
			print "Queue size: %d" % q.qsize()
		if not psp.is_alive():
			psp.join()
			psp =  PointStoreProcess(pointStore, options.nameserver, options.pointservice)
	#else:
	#	sock = ctx.socket(zmq.REQ)
	#	ns.connectService(sock, options.jobservice)
	#	for jobid in options.generategraphs.split(","):
	#		sock.send_multipart(("jobinfo", jobid))
	#		job = sock.recv()
	#		JobArchiveGenerator(pointStore, q, jobStore, True, extraFields={"cluster": options.cluster}).start()
	#		q.put(json.loads(job))
if __name__ == "__main__":
	main()
