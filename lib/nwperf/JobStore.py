#!/usr/bin/env python
import sys
import os
import tarfile
import time
import datetime

class JobStore(object):
	def fork(self):
		pass

	def jobProcessed(self):
		return false

	def storeJob(self):
		pass

	def processJob(self, job, points, additionalFields = {}, forceProcessing = False):
		self.job = job
		self.graphs = {}
		self.additionalFields = additionalFields
		twoMinutes = datetime.timedelta(0,120)
		oneMinute = datetime.timedelta(0,60)
		self.job["points"] = []
		if forceProcessing or not self.jobProcessed():
			hostTimes = {}
			startTime = int(time.strftime("%s", time.strptime(job["Start"], "%Y-%m-%dT%H:%M:%S")))
			endTime = int(time.strftime("%s", time.strptime(job["End"], "%Y-%m-%dT%H:%M:%S")))
			if endTime - startTime < 60:
				return
			count = 0
			for i in points:
				try:
					while hostTimes[i["host"]] + twoMinutes < i["timestamp"]:
						for metric in self.graphs.itervalues():
							metric[i["host"]].append((i["timestamp"], None))
						hostTimes[i["host"]] += oneMinute
				except KeyError:
					hostTimes[i["host"]] = i["timestamp"]
				hostTimes[i["host"]] = i["timestamp"]
				self.graphs.setdefault(i["metric"],{}).setdefault(i["host"],[]).append((i["timestamp"], i["value"]))
				count+=1

			if (count/len(job["hosts"])) > 2000:
				for (metric, job["hosts"]) in self.graphs.iteritems():
					downSampled = {}
					for (host, points) in job["hosts"].iteritems():
						numPoints = len(points)/100
						curPointCount = 0
						totalPointCount = 0
						sum = 0
						numHoles = 0
						for point in points:
							try:
								sum += point[1]
							except TypeError:
								numHoles += 1
							curPointCount += 1
							totalPointCount += 1
							if curPointCount >= numPoints:
								try:
									downSampled.setdefault(host,[]).append((startTime+totalPointCount*60,sum/(curPointCount-numHoles)))
								except ZeroDivisionError:
									downSampled.setdefault(host,[]).append((startTime+totalPointCount*60,None))
								sum = 0
								curPointCount = 0
						if curPointCount > 0:
							downSampled.setdefault(host,[]).append((startTime+totalPointCount*60000,sum/curPointCount))
						self.graphs[metric] = downSampled
							
					if metric not in self.job["points"]:
						self.job["points"].append(metric)
			self.storeJob()
		self.job = {}
		self.graphs = {}
		self.additionalFields = {}
