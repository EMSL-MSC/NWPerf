#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle "BSD-style" open source license;
# the full text of that license is available in the COPYING file in the root of the repository
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
		if forceProcessing or not self.jobProcessed():
			hostTimes = {}
			startTime = int(time.strftime("%s", time.strptime(job["Start"], "%Y-%m-%dT%H:%M:%S")))
			endTime = int(time.strftime("%s", time.strptime(job["End"], "%Y-%m-%dT%H:%M:%S")))
			if endTime - startTime < 60:
				return
			count = 0
			for i in points:
				try:
					while hostTimes[i["host"]] + oneMinute < i["time"]:
						hostTimes[i["host"]] += oneMinute
						for metric in self.graphs.itervalues():
							metric[i["host"]].append((hostTimes[i["host"]], None))
				except KeyError:
					hostTimes[i["host"]] = i["time"]
				hostTimes[i["host"]] = i["time"]
				self.graphs.setdefault(i["pointname"],{}).setdefault(i["host"],[]).append((i["time"], i["val"]))
				count+=1

			if (count/len(job["Nodes"])) > 2000:
				print "downsampling", count, len(job["Nodes"])
				for (metric, nodes) in self.graphs.iteritems():
					downSampled = {}
					for (host, points) in nodes.iteritems():
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
									downSampled.setdefault(host,[]).append( (
										datetime.datetime.fromtimestamp(startTime+totalPointCount*60),
										sum/(curPointCount-numHoles)
									))
								except ZeroDivisionError:
									downSampled.setdefault(host,[]).append( (
										datetime.datetime.fromtimestamp(startTime+totalPointCount*60),
										None
									))
								sum = 0
								curPointCount = 0
								numHoles = 0
						if curPointCount > 0:
							downSampled.setdefault(host,[]).append( (
								datetime.datetime.fromtimestamp(startTime+totalPointCount*60),
								sum/curPointCount
							))
						self.graphs[metric] = downSampled
			
							
			self.storeJob()
		self.job = {}
		self.graphs = {}
		self.additionalFields = {}
