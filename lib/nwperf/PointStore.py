# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle “BSD-style” open source license;
# the full text of that license is available in the COPYING file in the root of the repository
import time
import os
import struct
import array

class PointStore(object):
        def __init__(self, storeDir, socket = None):
                self.storeDir = storeDir
                self.oneday = 60*60*24
		self.curValues = {}
		if not os.path.exists(self.storeDir):
			os.makedirs(self.storeDir)
		self.headerStruct = struct.Struct("II")
		self.pointStruct = struct.Struct("IIf")
		self.fork()

	def fork(self):
		self.loadHosts()
		self.loadMetrics()

	def loadHosts(self):
		try:
			self.index2host = [i.rstrip() for i in open(self.storeDir+"/Hosts", "r")]
			self.host2index = dict([(host, index) for (index,host) in enumerate(self.index2host)])
		except IOError:
			self.index2host = []
			self.host2index = {}
		self.hostsUpdated = False

	def loadMetrics(self):
		try:
			self.index2metric = [i.rstrip() for i in open(self.storeDir+"/Metrics", "r")]
			self.metric2index = dict([(metric, index) for (index,metric) in enumerate(self.index2metric)])
		except IOError:
			self.index2metric = []
			self.metric2index = {}
		self.metricsUpdated = False

        def savePoint(self, host, metric, timestamp, value):
		value = float(value)
		try:
			metric = self.metric2index[metric]
		except KeyError:
			self.index2metric.append(metric)
			self.metric2index[metric] = metric = len(self.metric2index)
			self.metricsUpdated = True
		try:
			host = self.host2index[host]
		except KeyError:
			self.index2host.append(host)
			self.host2index[host] = host = len(self.host2index)
			self.hostsUpdated = True
		timestamp = int(timestamp)
		self.curValues.setdefault(timestamp/60*60, array.array("c")).extend(self.pointStruct.pack(host, metric, value))
			
	def flush(self):
		prevDay = 0
		f = None
		if self.metricsUpdated == True:
			open(self.storeDir+"/Metrics", "w").write("\n".join(self.index2metric))
			self.metricsUpdated = False
		if self.hostsUpdated == True:
			open(self.storeDir+"/Hosts", "w").write("\n".join(self.index2host))
			self.hostsUpdated = False
		for (minute, values) in self.curValues.iteritems():
			day = minute/self.oneday*self.oneday
			if prevDay != day:
				filename = "%s/%d" % (self.storeDir, day) 
				if f != None:
					f.close()
				f= open(filename, "a")
				prevDay = day
			f.write(self.headerStruct.pack(values.buffer_info()[1], minute))
			values.tofile(f)
		if f != None:
			f.close()
		self.curValues = {}

        def getMetrics(self):
		return self.index2metric

        def gethosts(self):
		return self.index2host

        def getPoints(self, beginTime, endTime, hosts = None, metrics = None):
		#print "getPoints", beginTime, endTime, hosts, metrics
		beginTime = int(beginTime)
		endTime = int(endTime)
		dayStart = beginTime / self.oneday * self.oneday 
		if hosts:
			try:
				hosts = [self.host2index[host] for host in hosts]
			except KeyError:
				self.loadHosts()
				hosts = [self.host2index[host] for host in hosts]
		else:
			hosts = self.host2index.values()
		if metrics:
			try:
				metrics = [self.metric2index[metric] for metric in metrics]
			except KeyError:
				self.loadMetrics()
				metrics = [self.metric2index[metric] for metric in metrics]
		else:
			metrics = self.metric2index.values()
		#print "dayStart", dayStart, "endTime+1", endTime+1
                for day in range(dayStart, endTime+1, self.oneday):
			try:
				#print "opening %s/%d" % (self.storeDir, day)
				f = open("%s/%d" % (self.storeDir, day), "r")
			except:
				continue
			data = f.read(self.headerStruct.size)
			if data < self.headerStruct.size:
				return
			(size, minute) = self.headerStruct.unpack(data)
			#print time.time(), "read: size", size, "minute", time.ctime(minute), "beginTime", beginTime
			endOfFile = False
			while minute < beginTime:
				#print time.time(), "seeking"
				f.seek(size, 1)
				data = f.read(self.headerStruct.size)
				if len(data) < self.headerStruct.size:
					#print "found end of the file"
					endOfFile = True
					break
				(size, minute) = self.headerStruct.unpack(data)
				#print time.time(), "read: size", size, "minute", time.ctime(minute), "beginTime", beginTime
			if endOfFile:
				continue
			#print time.time(), "found time slice"
			while minute <= endTime:
				#print time.time(), "reading %d bytes" % size
				data = f.read(size)
				if len(data) < size:
					break
				for entry in range(size/self.pointStruct.size):
					##print time.time(), "unpacking data point"
					(host, metric, value) = self.pointStruct.unpack_from(data, entry*self.pointStruct.size)
					if host in hosts and metric in metrics:
						yield { "host": self.index2host[host],
							"pointname": self.index2metric[metric],
							"time": minute,
							"val": value}
				data = f.read(self.headerStruct.size)
				if len(data) < self.headerStruct.size:
					break
				(size, minute) = self.headerStruct.unpack(data)
				#print time.time(), "read: size", size, "minute", time.ctime(minute), "beginTime", beginTime
if __name__ == "__main__":
	import time
	ps = PointStore("store")
	hosts = []
	for cu in range(1,13):
		for node in range(1, 195):
			hosts += ["cu%dn%d" % (cu, node)]
	count = 0
	data = []
	for timestamp in range(1352846721, 1352846721+(3600), 60):
		#print timestamp
		for host in hosts:
			for metric in ["metric%d" % i for i in range(150)]:
				data.append([host, metric, timestamp, count])
				count += 1
	start = time.time()
	for i in data:
		ps.savePoint(i[0], i[1], i[2], i[3])
	ps.flush()
	mid = time.time()
	hosts = hosts[100:150]
	for point in ps.getPoints(1352846721, 1352846721, hosts):
		##print point
		pass
	end = time.time()
	#print mid - start
	#print end - mid
