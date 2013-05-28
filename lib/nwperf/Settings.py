# -*- coding: latin-1 -*-
import os.path
try:   
	import simplejson as json
except:
	import json

class Settings(object):
	settings = False
	ftime = False
	def __init__(self, config):
		self.configfile = config
		self.load_config()

	def load_config(self):
		if self.settings == False:
			self.settings = json.load(open(self.configfile, "r"))
			self.ftime = os.path.getmtime(self.configfile)

	def __getitem__(self, key):
		if self.ftime != os.path.getmtime(self.configfile):
			self.load_config()

		return [i for i in self.settings if i["id"] == key][0]["value"]

	def __setitem__(self, key, item):
		item = [i for i in self.settings if i["id"] == key][0]["value"] = item
		json.dump(self.settings, open(self.configfile, "w"), indent=4)
		self.ftime = os.path.getmtime(self.configfile)

	def __iter__(self):
		if self.ftime != os.path.getmtime(self.configfile):
			self.load_config()
		for i in self.settings:
			yield (i["id"],i["value"])
			
	def add(self, key, vtype, value, label, info):
		d={'id':key,'value':value,'type':vtype}
		if label:
			d['label'] = label
		if info:
			d['description'] = info
		self.settings.append(d)
		json.dump(self.settings, open(self.configfile, "w"), indent=4)
		self.ftime = os.path.getmtime(self.configfile)

