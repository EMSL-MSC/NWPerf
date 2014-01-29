#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle "BSD-style" open source license;
# the full text of that license is available in the COPYING file in the root of the repository

import os
import sys
import socket
import subprocess
from nwperf import nnslib
import zmq
import nwperf
import time
import signal
import pickle
import datetime


apihelp="""JobDictionary can be one of two things, by requesting:
jobinfo <jobid> - returns a dictionary containing one job
running         - returns a dictionary containing all currently running jobs indexed by jobid
completed       - returns a dictionary of all jobs completed recently
"""
flds="JobID,NodeList,NCPUS,Submit,JobName,Priority,Start,NTasks,End,CPUTime,State,UID,Elapsed,Partition,GID,SystemCPU,UserCPU,ExitCode,Account,User"
notifyfields=flds.split(",")
def timeToSeconds(hms):
	#print hms
	dayflag = hms.find('-')
	if dayflag != -1:
		days=int(hms[:dayflag])
	else:
		days=0
	t = datetime.timedelta(days=days,hours=int(hms[-8:-6]),minutes=int(hms[-5:-3]),seconds=int(hms[-2:]))
	return t.seconds+t.days*86400

def isoToEpoch(iso):
	try:
		t = datetime.datetime.strptime(iso,'%Y-%m-%dT%H:%M:%S')
		return time.mktime(t.timetuple())
	except ValueError:
		return 0

def suckJobInfo(jobnumber):
	sp = subprocess.Popen(["/usr/bin/sacct",'-X','-P','-o',flds,'-j',jobnumber],stdout=subprocess.PIPE)
	jobs = suckJobs(sp)
	try:
		return jobs[jobnumber]
	except:
		return {}

def runningJobInfo():
	sp = subprocess.Popen(["/usr/bin/sacct",'-X','-P','-s','r','-a','-o',flds],stdout=subprocess.PIPE)
	jobs = suckJobs(sp)
	return jobs


def suckJobs(process):
	infodb = {}
	headers = process.stdout.readline().rstrip().split("|")
	lines = process.stdout.readlines()
	for line in lines:
		line=line.rstrip()
		parts = line.split("|")
		themap=dict(zip(headers,parts))
		try:
			infodb[themap['JobID']].update(themap)
		except KeyError:
			infodb[themap['JobID']]=themap
	return infodb

class JobStatus:
	def __init__(self,zmqsock,statefile="/tmp/slurmjobs.state"):
		self.sock = zmqsock
		self.running = {}
		self.completed = {}
		self.lastupdate = 0
		self.statefile = statefile
		self.loadState()
		self.checkUpdate()

	def jobInfo(self,jid):
		self.checkUpdate()
		if jid in self.running:
			return self.running[jid]
		if jid in self.completed:
			return self.completed[jid]
		return suckJobInfo(jid)

	def runningJobs(self):
		self.checkUpdate()
		return self.running

	def completedJobs(self):
		self.checkUpdate()
		return self.completed
		
	def checkUpdate(self):
		if self.lastupdate + 30 > time.time():
			return
		print "checkUpdate"
		currentRunningJobs = runningJobInfo()
		current = currentRunningJobs.keys()
		old = self.running.keys()
		for jid in old:
			if jid not in current:
				print "job Complete",jid
				self.completed[jid] = suckJobInfo(jid)  #get the latest info about it
				self.sock.send("JobEnd", zmq.SNDMORE)
				self.sock.send_json(self.completed[jid])
		for jid in current:
			if jid not in old:
				print "new job",jid
				self.sock.send("JobStart", zmq.SNDMORE)
				self.sock.send_json(currentRunningJobs[jid])

		self.running=currentRunningJobs
		self.lastupdate = time.time()

		#fixme: expire old completed here
		for jid in self.completed.keys():
			job = self.completed[jid]
			if isoToEpoch(job["Start"])+timeToSeconds(job["Elapsed"]) < self.lastupdate-86400:
				print "Expiring Job:",job["JobID"]
				del(self.completed[jid])

		self.saveState()
	
	def saveState(self):
		try:
			pickle.dump((self.running,self.completed),open(self.statefile,'w'))	
			print "Saved",len(self.running.keys()),"running, and",len(self.completed.keys()),"Completed jobs to statefile"
		except Exception,msg:
			print "error loading state file",msg

	def loadState(self):
		try:
			self.running,self.completed = pickle.load(open(self.statefile,'r'))	
			print "Loaded",len(self.running.keys()),"running, and",len(self.completed.keys()),"Completed jobs from statefile"
		except Exception,msg:
			print "error loading state file",msg
		


def main(nsurl,cname,myip,statefile):
	global running
	timeout=600
	ctx = zmq.Context()
	sock = ctx.socket(zmq.REP)
	port = sock.bind_to_random_port("tcp://%s"%(myip))
	notifysock = ctx.socket(zmq.PUB)
	notifyport = notifysock.bind_to_random_port("tcp://%s"%(myip))
	
	ns = nnslib.NameServer(nsurl)
	try:
		dt = ns.getDataType("JobDictionary")
	except nnslib.NameServerException:
		ns.addDataType("JobDictionary","JSON",','.join(notifyfields),"")

	ns.publishService(cname+".slurm.jobinfo","tcp://%s:%s"%(myip,port),600,"req/rep","JobDictionary")
	ns.publishService(cname+".slurm.jobnotify","tcp://%s:%s"%(myip,notifyport),600,"pub/sub","JobDictionary")

	z_poll = zmq.core.Poller()
	z_poll.register(sock,zmq.POLLIN)
	z_poll.register(notifysock,zmq.POLLIN)

	status = JobStatus(notifysock,statefile)

	running = True
	def doStop(num=None,frame=None):
		global running
		running=False
		try:
			ns.removeServices()
		except zmq.ZMQError:
			pass
	signal.signal(signal.SIGTERM, doStop)
	signal.signal(signal.SIGINT, doStop)

	while running:
		try:
			ready = z_poll.poll(60)
		except zmq.ZMQError:
			ready = []
		#print ready
		if ready and ready[0][0]==sock:
			request = sock.recv_multipart()
			try:
				print request
				if request[0] == "jobinfo":
					info = status.jobInfo(request[1])
					sock.send_json(info)		
				if request[0] == "running":
					info = status.runningJobs()
					sock.send_json(info)
				if request[0] == "completed":
					info = status.completedJobs()
					sock.send_json(info)
			except:
				sock.send_json({})
			print "done"
		else:
			ns.updateServices()
			status.checkUpdate()

if __name__ == "__main__":
	myip = socket.gethostbyname(socket.gethostname())
	parser = nwperf.defaultServerOptionParser()
	parser.add_option("-S","--name-server",dest="nameserver",type="string",help="The ZMQ URL of the nameserver to register with",default="tcp://nwperf-ns:6967")
	parser.add_option("-s","--state-file", help="File to store the current slurm state", dest="statefile", default="/tmp/slurmjobs.state")
	parser.add_option("-c","--cluster",dest="cluster",type="string",help="The cluster prefix to publish as",default=None)
	parser.add_option("-i", "--ip", dest="ip", type="string", help="ip address to bind to. default: %s" % myip, default=myip)

	options,args = nwperf.parseServerOptions()

	if not options.cluster:
		parser.error("No Cluster Specified")

	main(options.nameserver,options.cluster,options.ip,options.statefile)
