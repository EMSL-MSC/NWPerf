#!/usr/bin/env python
import sys
import os
import tarfile
import time
import hostlist
import multiprocessing
import datetime
from nwperf import nnslib
from nwperf import PointStore, ArchiveJobStore
from nwperf import MongoPointStore, MongoJobStore
from nwperf import Settings
import nwperf
import zmq
try:
	import cStringIO as StringIO
except ImportError:
	import StringIO
try:
	import simplejson as json
except ImportError:
	import json

job = {"Account":"mscfops","NodeList":"cu12n129","UID":"22054","Elapsed":"00:02:00","UserCPU":"00:00:00","NCPUS":"8","Partition":"tiny","State":"COMPLETED","Submit":"2013-01-28T16:44:17","JobName":"moab.job.Uke1LM","Priority":"0","Start":"2013-01-28T16:44:43","NTasks":"","GID":"100","CPUTime":"00:16:00","User":"kschmidt","End":"2013-01-28T16:46:43","JobID":"1844347","SystemCPU":"00:00:00","ExitCode":"0:0"}
pointStore = MongoPointStore.MongoPointStore()
jobStore = MongoJobStore.MongoJobStore()
job["hosts"] = hostlist.expand_hostlist(job["NodeList"])
start = datetime.datetime.strptime(job["Start"], "%Y-%m-%dT%H:%M:%S")
end = datetime.datetime.strptime(job["End"], "%Y-%m-%dT%H:%M:%S")
points = pointStore.getPoints(start, end, job["hosts"])
jobStore.processJob(job, points, {"cluster": "chinook"})
