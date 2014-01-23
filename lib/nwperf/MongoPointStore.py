# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle "BSD-style" open source license;
# the full text of that license is available in the COPYING file in the root of the repository
import datetime
import os
import pymongo

class MongoPointStore(object):
        def __init__(self, mongouri = None):
		self.mongouri = mongouri
		self.fork()
		if not "points" in self.db.collection_names():
			self.db.points.ensure_index("time", pymongo.ASCENDING, unique=False, expireAfterSeconds=3600*24*30) 
			#self.db.points.ensure_index([("time", pymongo.ASCENDING), ("host", pymongo.ASCENDING)], unique=False, expireAfterSeconds=300) 
		self.curValues = {}

	def fork(self):
		if self.mongouri:
			self.db = pymongo.Connection(self.mongouri)
		else:
			self.db = pymongo.Connection().nwperf
		

        def savePoint(self, host, metric, timestamp, value):
		value = float(value)
		timestamp = int(float(timestamp))
		self.curValues.setdefault(timestamp/60*60, {}).setdefault(host,[]).append((metric, value))
			
	def flush(self):
		for timestamp in self.curValues:
			time = datetime.datetime.fromtimestamp(timestamp)
			for host in self.curValues[timestamp]:
				self.db.points.insert({"time": time, "host": host, "points": self.curValues[timestamp][host]})
		self.curValues = {}

        def getPoints(self, beginTime, endTime, hosts = None, metrics = None):
		try:
			endTime = datetime.datetime.fromtimestamp(endTime/60*60)
		except TypeError:
			pass
		try:
			beginTime = datetime.datetime.fromtimestamp(beginTime/60*60)
		except TypeError:
			pass
		print "Finding points:", {"time": {"$gte": beginTime, "$lte": endTime}, "host": {"$in": hosts}}
		entries = self.db.points.find({"time": {"$gte": beginTime, "$lte": endTime}, "host": {"$in": hosts}})
		for entry in entries:
			for point in entry["points"]:
				yield { "host": entry["host"],
					"pointname": point[0],
					"time": entry["time"],
					"val": point[1]}
if __name__ == "__main__":
	import time
	ps = MongoStore()
	hosts = []
	for cu in range(1,13):
		for node in range(1, 195):
			hosts += ["cu%dn%d" % (cu, node)]
	count = 0
	data = []
	reftime = int(time.time())
	for timestamp in range(reftime, reftime+(60), 60):
		print timestamp
		for host in hosts:
			for metric in ["metric%d" % i for i in range(150)]:
				data.append([host, metric, timestamp, count])
				count += 1
	start = time.time()
	print "Saving points"
	for i in data:
		ps.savePoint(i[0], i[1], i[2], i[3])
	print "flushing points"
	ps.flush()
	print "finished"
	mid = time.time()
	hosts = hosts[100:102]
	for point in ps.getPoints(reftime, reftime+60, hosts):
		print point
		pass
	end = time.time()
	print mid - start
	print end - mid
