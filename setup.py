#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle "BSD-style" open source license;
# the full text of that license is available in the COPYING file in the root of the repository

import os
from distutils.core import setup
from distutils.command.install_scripts import install_scripts
from distutils.command.build_scripts import build_scripts
from distutils.util import convert_path
from glob import glob


class local_install_scripts(install_scripts):
	def finalize_options(self):
		install_scripts.finalize_options(self)
		#remove the bin part of the install dir, so we can use sbin and bin
		if os.path.basename(self.install_dir) == 'bin':
			self.install_dir =  os.path.dirname(self.install_dir)

class local_build_scripts(build_scripts):

	def initialize_options(self):
		build_scripts.initialize_options(self)

	def mkbld(self,thedir):
		b = build_scripts(self.distribution)
		b.build_dir = self.build_dir+thedir
		b.scripts = []
		b.force = self.force
		b.executable = self.executable
		b.outfiles = None
		return b

	def finalize_options(self):
		build_scripts.finalize_options(self)
		# build up a dictionary of commands for sub scripting
		self.blds={}
		
		print self.scripts
		for file in self.scripts:
			d,f = file.split('/',1)
			if not self.blds.has_key(d):
				self.blds[d]=self.mkbld('/'+d)
			print convert_path(f)
			self.blds[d].scripts += [file]

		#for k,v in self.blds.items():
		#	print k,'=>',self.blds[k].scripts,self.blds[k].build_dir

	def run(self):
		for k,v in self.blds.items():
			v.run()


setup(	name = "nwperf",
		version = "0.5",
		description = "A set of utilities for gathering and stroing performance information for clusters of computers",
		author = "EMSL MSC team",
		url = "https://github.com/EMSL-MSC/NWPerf/",
		packages = ["nwperf"],
		package_dir = {'nwperf':'lib/nwperf'},
		scripts = [
			#"fp_wsgi.py",# this should be in a web directory or some such... fixme
			"sbin/nwperf-ganglia.py",
			"bin/gen_cview",
			#"generateFlotGraph.py",  kenny will deal with this
			"bin/getjobinfo",
			#"jobpacker-zmq.py", ???
			#"moab-zmq.py", probably should keep
			#"nwperf-mq.py",   dont need it
			"sbin/nwperf-ns.py",
			"bin/nwperf-nsq.py",
			"sbin/nwperfconfig",
			#"nwperf-zmq.py", old, probably dont need
			"sbin/nwperf-ceph-store.py",
			"sbin/slurmjob-zmq.py",
		],
		data_files=[
			("/etc/",["conf/nwperf.conf"]),
			("/etc/rc.d/init.d/", ["sysvinit/nwperf"]),
			("/etc/init",glob("upstart/*.conf"))
		],
		cmdclass = {
			'install_scripts': local_install_scripts,
			'build_scripts': local_build_scripts,
		}	
	)

#requires: python-zmq
