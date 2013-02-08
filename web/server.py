CONFIG="/etc/nwperf.conf"

import os
import datetime
import web
import pymongo
import bson
try:
	import simplejson as json
except:
	import json
import calendar

def is_admin(user = None):
	if user == None:
		user = get_user()
	if settings["dbFormat"] == "NWPerf":
		res = db.select("usergroups", where="nwperf_user = $user and nwperf_group = 'admin'", vars={"user": user})
		return len(res) > 0
	else:
		return user in settings["admins"].split(",")

def get_user():
	try:
		#kerberos hack... Don't know if this is the right way
		return web.ctx.env["REMOTE_USER"].split("@")[0]
	except:
		return web.ctx.env["REMOTE_USER"]

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
		if key == "dbFormat":
			return "mongo"
		if self.ftime != os.path.getmtime(self.configfile):
			self.load_config()

		return [i for i in self.settings if i["id"] == key][0]["value"]

	def __setitem__(self, key, item):
		item = [i for i in self.settings if i["id"] == key][0]["value"] = item
		json.dump(self.settings, open(self.configfile, "w"), indent=4)
		self.ftime = os.path.getmtime(self.configfile)

class SettingsWeb(Settings):
	def __init__(self):
		super(SettingsWeb, self).__init__(CONFIG)
		
	def GET(self, setting):
		tag = web.input(tag=0).tag
		if setting == "":
			return json.dumps({
					"settings": [i for i in self.settings if i["id"] != "metrics"],
					"tag": tag
				}
				,separators=(',', ':'))
		else:
			try:
				return json.dumps({
						"setting": [i for i in self.settings if i["id"] == setting][0],
						"tag": tag
					}
					,separators=(',', ':'))
			except IndexError:
				return web.NotFound()

	def PUT(self, setting):
		if is_admin():
			try:
				if setting != "metrics":
					self[setting] = web.input()["value"]
					if setting in ("dbtype", "dbhost", "dbname", "dbuser", "dbpass", "dbport"):
						try:
							db = web.database(dbn=settings["dbtype"], host=settings["dbhost"], db=settings["dbname"], user=settings["dbuser"], password=settings["dbpass"], port=int(settings["dbport"]))
						except ValueError:
							db = web.database(dbn=settings["dbtype"], host=settings["dbhost"], db=settings["dbname"], user=settings["dbuser"], password=settings["dbpass"])
							
					return json.dumps({"status": "OK", "message": "Setting Updated"})
			except KeyError:
				pass
		return web.Forbidden()

def encode_datetime(obj):
	if isinstance(obj, datetime.datetime):
		return str(obj)
	elif isinstance(obj, datetime.timedelta):
		return str(obj)
	elif isinstance(obj, bson.ObjectId):
		return str(obj)
	raise TypeError(repr(obj) + " is not JSON serializable")

class Cview(object):
	def GET(self, id):
		id = int(id)
		user = get_user()

		jobOwner = True

                file = os.path.join(settings["cviewdir"], str(id%100), str(id/100%100), "%d.tar.gz" %id)
                cviewAvail = os.path.exists(file)

		ret = ""
		if (jobOwner or is_admin(user)) and cviewAvail:
			web.header('Content-type', 'application/x-cviewall')
			web.header('Content-Disposition', 'attachment; filename="%d.cviewall"' % id)
			ret  = '{\n'
			ret += '\turl = "http://pic-view.pnl.gov/cgi-bin/fp_ceph_job.cgi/pic/%d/";\n' % id
			ret += '\tmetrics = ("cputotals.user", "meminfo.used");\n'
			ret += '\tdataUpdateInterval = 0.0;\n'
			ret += '}\n'
		return ret

def encode_datetime_to_javascript(obj):
	if isinstance(obj, datetime.datetime):
		return calendar.timegm(obj.utctimetuple())*1000

class Graph(object):
	def GET(self, id, metric):
		try:
			job = db.jobs.find_one({"_id": bson.objectid.ObjectId(id)})
			for graph in job["graphs"]:
				if graph["name"] == metric:
					return json.dumps(db.graphs.find_one({"_id": graph["graph"]}, {"_id": False, "job": False}), default=encode_datetime_to_javascript)
		except IOError:
			import phpserialize
			id = int(id)
			pointsDir = os.path.join(settings["graphsdir"], str(id%100), str(id/100%100), str(id))
			pointsDescFile = os.path.join(pointsDir, "pointsDescriptions")
			jobData = phpserialize.load(open(pointsDescFile))
			for graph in jobData.values():
				if graph["name"] == metric:
					pointGraph = os.path.join(pointsDir, "job.%d-point.%s.png"% (id, graph["point_id"]))
					break
			try:
				web.header("content-Type", "image/png")
				return open(pointGraph).read()
			except:
				pass

class GroupMembership(object):
	def GET(self, user):
		if user == "":
			user = get_user()
		if user in settings["admins"].split(","):
			return json.dumps(["admin"])

class Metrics(object):
	def GET(self, name):
		tag = web.input(tag=0).tag
		if name != "":
			return json.dumps({"tag": tag, "metric": ""})
			metric = db.metrics.find_one({"name": name}, {"_id": False})
			if metric:
				return json.dumps({"tag": tag, "metric": metric})
			else:
				return web.NotFound()
		else:
			return json.dumps({"tag": tag, "metrics": tuple(db.metrics.find({},{"_id": False}))})
	def PUT(self, name):
		if not is_admin():
			return web.Forbidden()

		metric = web.input()
		res = db.metrics.update({"name": name}, metric, True)
		return json.dumps({"status": "OK", "message": "Metric Updated"})

	def DELETE(self, name):
		if not is_admin():
			return web.Forbidden()

		db.metrics.remove({"name": name})
		return json.dumps({"status": "OK", "message": "Metric Deleted"})

class Jobs(object):
	def GET(self, job):
		input = web.input(q=None)
		tag = input.tag
		query = input.q
		if query != None:
			query = json.loads(query)
			if not is_admin():
				query.append(("User", get_user()))
			months = {	"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
					"Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
			fields = {	"Start Date": "startTime", "End Date": "endTime",
					"Submit Date": "submitTime", "Node Count": "numHosts",
					"User": "user", "Job Id": "id", "Account": "account"}
			comps = {"<": "$lt", ">": "$gt", "<=": "$lte", ">=": "$gte"}
			mongoQuery = {}
			for queryItem in query:
				try:
					column = fields[queryItem[0]]
				except:
					pass
				if queryItem[0] in ("Start Date", "End Date", "Sumbit Date"):
					try:
						if queryItem[1] == "<":
							date = datetime.datetime(queryItem[4], months[queryItem[2]], queryItem[3], 23, 59, 59)
						elif queryItem[1] == ">":
							date = datetime.datetime(queryItem[4], months[queryItem[2]], queryItem[3], 0, 0, 0)
						else:
							continue
					except ValueError:
						continue
					if queryItem[1] == "==":
						mongoQuery[column] = date
					else:
						mongoQuery.setdefault(column, {})[comps[queryItem[1]]] = date
				elif queryItem[0] ==  "Node Count":
					if queryItem[1] in comps:
						mongoQuery.setdefault(column, {})[comps[queryItem[1]]] = int(queryItem[2])
					elif queryItem[1] == "==":
						mongoQuery[column] = (queryItem[2])
				elif queryItem[0] in ("Job Id"):
					mongoQuery[column] = int(queryItem[1])
				elif queryItem[0] in ("Account", "User"):
					mongoQuery[column] = queryItem[1]
				elif queryItem[0] == "Ran On Node":
					mongoQuery.setdefault("hosts",{"$in": []})["$in"].append(queryItem[1])
			project = {	"account": True,
					"numHosts": True,
					"submitTime": True,
					"endTime": True,
					"user": True,
					"startTime": True,
					"runTime": True,
					"id": True}
			if len(mongoQuery) > 0:
				ret = tuple(db.jobs.find(mongoQuery, project))
				for i in ret:
					i["jobid"] = i["_id"]
					del(i["_id"])
				print ret
				return json.dumps({"tag": tag, "jobs": ret}, default=encode_datetime)
			else:
				return json.dumps({"tag": tag, "jobs": []})
	
		else:
			metrics = db.metrics.find()
			metrics = dict([(metric["name"], metric) for metric in metrics])

			job = db.jobs.find_one({"_id": bson.objectid.ObjectId(job)})
			graphs = job["graphs"]
			job["graphs"] = {}
			for graph in graphs:
				graphname = graph["name"]
				try:
					job["graphs"].setdefault(metrics[graphname]["group"],[]).append({
									"src": "graphs/%s/%s" % (str(job["_id"]),graph["name"]),
									"name": graphname,
									"unit": metrics[graphname]["unit"],
									"description": metrics[graphname]["description"]})
				except KeyError, e:
					job["graphs"].setdefault("other",[]).append({
									"src": "graphs/%s" % graph["name"],
									"name": graphname})
			job["tag"] = tag
			job["version"] = 2
			job["jobid"] = str(job["_id"])
			del(job["_id"])
			return json.dumps(job, default=encode_datetime)

class Users(object):
	def GET(self):
		if is_admin():
			res = db.select("moab_job_details", what="distinct moab_job_details.user as user")
			return json.dumps([i["user"] for i in res])
		else:
			return json.dumps([get_user()])
urls = (
    '/cview/(\d+)', 'Cview',
    '/graphs/([^/]+)/(.*)', 'Graph',
    '/groupMembership/(.*)', 'GroupMembership',
    '/metrics/(.*)', 'Metrics',
    '/settings/(.*)', 'SettingsWeb',
    '/jobs/(.*)', 'Jobs',
    '/users/', 'Users'
)

settings = Settings(CONFIG)
#db = pymongo.Connection(settings["dbhost"], settings["dbport"])[settings["dbname"]]
db = pymongo.Connection().nwperf
app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()
