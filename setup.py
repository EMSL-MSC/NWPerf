#!/usr/bin/env python

from distutils.core import setup
from glob import glob

setup(	name = "nwperf",
		version = "0.1",
		description = "A set of utilities for gathering and stroing performance information for clusters of computers",
		author = "EMSL MSC team",
		url = "https://github.com/EMSL-MSC/NWPerf/",
		packages = ["nwperf"],
		package_dir = {'nwperf':'lib/nwperf'},
		scripts = [
			#"fp_wsgi.py",# this should be in a web directory or some such... fixme
			#"ganglia-zmq.py",
			#"gen_cview",
			#"generateFlotGraph.py",
			#"getjobinfo-zmq.py",
			#"jobpacker-zmq.py",
			#"moab-zmq.py",
			#"nwperf-mq.py",
			"sbin/nwperf-ns.py",
			"bin/nwperf-nsq.py",
			"sbin/nwperfconfig",
			#"nwperf-zmq.py",
			#"point-ceph-store.py",
			#"PointStore.py",
			#"slurmjob-zmq.py",
		],
		data_files=[
			("/etc/",["conf/nwperf.conf"]),
			("/etc/init",glob("upstart/*.conf"))
		]
	)

#requires: python-zmq
