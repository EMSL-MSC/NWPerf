#!/usr/bin/env python
import os
import tarfile
import time
import JobStore
import pymongo
import datetime

class MongoJobStore(JobStore.JobStore):
	def __init__(self, mongouri = None):
		self.mongouri = mongouri
		self.fork()
		super(MongoJobStore, self).__init__()

	def fork(self):
		if self.mongouri:
			self.db = pymongo.Connection(self.mongouri)
		else:
			self.db = pymongo.Connection().nwperf

	def jobProcessed(self):
		return self.db.jobs.find({"id": int(self.job["JobID"]), "startTime": datetime.datetime.strptime(self.job["Start"], "%Y-%m-%dT%H:%M:%S")}).count()

	def storeJob(self):
		self.job["JobID"] = int(self.job["JobID"])
		endTime = datetime.datetime.strptime(self.job["End"], "%Y-%m-%dT%H:%M:%S")
		startTime = datetime.datetime.strptime(self.job["Start"], "%Y-%m-%dT%H:%M:%S")
		submitTime = datetime.datetime.strptime(self.job["Submit"], "%Y-%m-%dT%H:%M:%S")
		metadata = {	"hosts":	self.job["hosts"].keys(),
				"numHosts":	len(self.job["hosts"]),
				"id":		self.job["JobID"],
				"account":	self.job["Account"],
				"submitTime":	submitTime,
				"endTime":	endTime,
				"startTime":	startTime,
				"runTime":	(endTime - startTime).seconds,
				"user":		self.job["User"],
				"graphs":	[]}
		metadata.update(self.additionalFields)
		_id = self.db.jobs.insert(metadata)
		graphs=[]
		for graph in self.graphs:
			self.graphs[graph]["job"] = _id
			graphs.append({"name": graph, "graph": self.db.graphs.insert(self.graphs[graph])})
		self.db.jobs.update({"_id": _id}, {"$set": {"graphs": graphs}})
