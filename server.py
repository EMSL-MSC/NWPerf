CONFIG="/etc/nwperf.conf"

import os
import datetime
import tarfile
import web
try:
	import simplejson as json
except:
	import json

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
		if self.ftime != os.path.getmtime(self.configfile):
			self.load_config()

		return [i for i in self.settings if i["id"] == key][0]["value"]

	def __setitem__(self, key, item):
		item = [i for i in self.settings if i.id == key][0]["value"] = item
		json.dump(self.settings, open(self.configfile, "w"), indent=4)
		self.ftime = os.path.getmtime(self.configfile)

class SettingsWeb(settings.Settings):
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
					return json.dumps({"status": "OK", "message": "Setting Updated"})
			except KeyError:
				pass
		return web.Forbidden()

def encode_datetime(obj):
	if isinstance(obj, datetime.datetime):
		return str(obj)
	elif isinstance(obj, datetime.timedelta):
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

class Graph(object):
	def GET(self, id, metric):
		pointArchiveDir = os.path.join(settings["tempdir"],"flot",id)
		try:
			return open(os.path.join(pointArchiveDir, "%s.flot" % metric)).read()
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
		if settings["dbFormat"] == "NWPerf":
			res = db.select("usergroups", what="nwperf_group", where="nwperf_user = $user", vars={"user": user})
			return json.dumps([i["nwperf_group"] for i in res])
		else:
			res = []
			if user in settings["admins"].split(","):
				return json.dumps(["admin"])

class Metrics(object):
	def GET(self, name):
		tag = web.input(tag=0).tag
		if name != "":
			res = db.select("point_descriptions, point_groups",
					what="point_description as description, point_name as name, units as unit, point_groups.name as group",
					where="point_descriptions.point_groups_id = point_groups.id and point_name = $name",
					vars={"name": name})
			if len(res) > 0:
				return json.dumps({"tag": tag, "metric": res[0]})
			else:
				return web.NotFound()
		else:
			res = db.select("point_descriptions, point_groups",
					what="point_description as description, point_name as name, units as unit, point_groups.name as group",
					where="point_descriptions.point_groups_id = point_groups.id and active = true")
			return json.dumps({"tag": tag, "metrics": tuple(res)})
	def PUT(self, name):
		if not is_admin():
			return web.Forbidden()

		metric = web.input()
		res = db.select("point_groups", what="id", where="name = $group", vars={"group": metric["group"]})
		if len(res) == 0:
			groupId = db.insert("point_groups", name=metric["group"])
		else:
			groupId = res[0]["id"]
			
		numUpdated = db.update("point_descriptions",
					where="point_name=$name",
					vars={"name": metric["name"]},
					point_name=metric["name"],
					point_description=metric["description"],
					units=metric["unit"],
					point_groups_id=groupId,
					active=True)
		if numUpdated != 0:
			return json.dumps({"status": "OK", "message": "Metric Updated"})
		else:
			db.insert("point_descriptions",
					point_name=metric["name"],
					point_description=metric["description"],
					units=metric["unit"],
					point_groups_id=groupId,
					active=True)
			return json.dumps({"status": "OK", "message": "Metric Added"})

	def DELETE(self, name):
		if not is_admin():
			return web.Forbidden()

		db.update("point_descriptions", where="point_name=$name", vars={"name": name}, active=False)
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
			if settings["dbFormat"] == "NWPerf":
				fields = {	"Start Date": "start_time", "End Date": "end_time", "Submit Date": "submit_time",
						"Node Count": "num_nodes_allocated", "User": "moab_job_details.user",
						"Job Id": "jobs.job_id", "Account": "account"}
				where = ["jobs.id = moab_job_details.jobs_id"]
			elif settings["dbFormat"] == "Slurm":
				fields = {	"Start Date": "time_start", "End Date": "time_end", "Submit Date": "time_submit",
						"Node Count": "nodes_alloc", "User": "user",
						"Job Id": "id_job", "Account": "account"}
				where = ["%s_job_table.id_assoc = %s_assoc_table.id_assoc" % ((settings["cluster"],)*2), "time_end != 0" ]
			runonnodes = []
			for queryItem in query:
				try:
					column = fields[queryItem[0]]
				except:
					pass
				if queryItem[0] in ("Start Date", "End Date", "Sumbit Date"):
					if queryItem[1] not in  ("<", ">"):
						continue
					if settings["dbFormat"] == "NWPerf":
						if queryItem[0] == "End Date":
							date = web.db.SQLParam("%s-%s-%s 23:59:59" % (queryItem[4], months[queryItem[2]], queryItem[3]))
						else:
							date = web.db.SQLParam("%s-%s-%s 00:00:00" % (queryItem[4], months[queryItem[2]], queryItem[3]))
						where.append(	"%s %s '%s'" % (column, queryItem[1], date))
					elif settings["dbFormat"] == "Slurm":
						if queryItem[0] == "End Date":
							date = datetime.date(int(queryItem[4]), int(months[queryItem[2]]), int(queryItem[3])).strftime("%s")
							date = int(date) + 86400
						else:
							date = datetime.date(int(queryItem[4]), int(months[queryItem[2]]), int(queryItem[3])).strftime("%s")
						where.append(	"%s %s '%s'" % ( column, queryItem[1], date))
				elif queryItem[0] ==  "Node Count":
					if queryItem[1] not in  ("<", ">", "==", "<=", ">="):
						continue
					where.append("%s %s %s" % (column, queryItem[1], web.db.SQLParam(queryItem[2])))
				elif queryItem[0] in ("Job Id", "Account", "User"):
					where.append("%s = '%s'" % (column, web.db.SQLParam(queryItem[1])))
				elif queryItem[0] == "Ran On Node":
					if settings["dbFormat"] == "NWPerf":
						where.append("moab_job_details.jobs_id in (select job_id from host_jobs, hosts where host_jobs.host_id = hosts.id and hosts.host_name = '%s')" % web.db.SQLParam(queryItem[1]))
					else:
						runonnodes.append(queryItem[1])
			if settings["dbFormat"] == "NWPerf":
				ret = db.select(["moab_job_details", "jobs"],
						what="jobs.job_id as id, moab_job_details.user as user, 'chinook-'||job_id||'-'||extract(epoch from start_time) as jobId, account, num_nodes_allocated as numNodes, submit_time as submitTime, start_time as startTime, end_time as endTime, end_time-start_time as runTime",
						where=" and ".join(where))
			elif settings["dbFormat"] == "Slurm":
				import hostlist
				ret = db.select([settings["cluster"]+"_job_table", settings["cluster"]+"_assoc_table"],
						what="id_job as id, user, id_job as jobid, account, nodes_alloc as numnodes, FROM_UNIXTIME(time_submit) as submittime, FROM_UNIXTIME(time_start) as starttime, FROM_UNIXTIME(time_end) as endtime, TIMEDIFF(FROM_UNIXTIME(time_end), FROM_UNIXTIME(time_start)) as runtime, nodelist",
						where=" and ".join(where))
				for node in runonnodes:
					ret = [i for i in ret if node in hostlist.expand_hostlist(i["nodelist"])]
			return json.dumps({"tag": tag, "jobs": tuple(ret)}, default=encode_datetime)
	
		else:
			(cluster, jobnum, starttime) = job.split("-")
			jobnum = int(jobnum)
			starttime = int(starttime)
			if ".." in cluster:
				return json.dumps({"error": "Invalid job id"})
			#file = os.path.join(settings["cviewdir"], str(job%100), str(job/100%100), "%d.tar.gz" % job)
			#cview = {True: "cview/%s" % job, False: False}[True]
			cview = False

			pointsArchive = os.path.join(settings["flotgraphsdir"], str(jobnum%100), str(jobnum/100%100), "%s.tar.bz2" % job)
			if not os.path.exists(pointsArchive): 
				try:
					ret = db.select(["jobs", "moab_job_details"],
							what="jobs.id as id",
							where="jobs.id = moab_job_details.jobs_id and job_id = $id and start_time = TIMESTAMP WITH TIME ZONE 'epoch' + $starttime * INTERVAL '1 second'",
							vars={"id": jobnum, "starttime": starttime})
					job = ret["id"]
					pointsDir = os.path.join(settings["graphsdir"], str(job%100), str(job/100%100), str(job))
					pointsDescFile = os.path.join(pointsDir, "pointsDescriptions")
					import phpserialize
					jobData = phpserialize.load(open(pointsDescFile))
					ret = {}
					for graph in jobData.values():
						if os.path.exists(os.path.join(pointsDir, "job.%s-point.%s.png" % (job, graph["point_id"]))):
							res = db.select("point_descriptions", what="point_description", where="id = $id", vars={"id": graph["point_id"]})
							ret.setdefault(graph["group"],[]).append({	"name": graph["name"],
													"src": "graphs/%s/%s" % (job, graph["name"]),
													"description": res[0]["point_description"]})
					return json.dumps({"version": 1, "graphs": ret, "cview": cview, "tag": tag})
				except:
					return json.dumps({"version": 1, "graphs": [], "cview": False, "tag": tag})
			else:
				graphs = {}
				pointsDir = os.path.join(settings["tempdir"], "flot")
				if not os.path.exists(pointsDir):
					os.mkdir(pointsDir)
				pointsDir = os.path.join(pointsDir,str(job))
				if not os.path.exists(pointsDir):
					tar = tarfile.open(pointsArchive)
					tar.extractall(pointsDir)
				try:
					jobmetadata = json.load(open(os.path.join(pointsDir, "metadata")))
				except:
					return json.dumps({"error": "Error reading job metadata", "tag": tag})
				for point in jobmetadata["points"]:
					if settings["dbFormat"] == "NWPerf":
						res = db.select("point_descriptions pd, point_groups pg",
							what="point_description as description, name as group, pd.units as units",
							where="pd.point_groups_id = pg.id and point_name = $point and active = true",
							vars={"point": point})
						try:
							row = res[0]
							group = row["group"]
							unit = row["units"]
							description = row["description"]
						except IndexError:
							group = "other"
							unit = None
							description = None
					elif settings["dbFormat"] == "Slurm":
						try:
							#TODO add metrics to config
							group = metadata["pointDescriptions"][point]["group"]
							unit = metadata["pointDescriptions"][point]["unit"]
							description = metadata["pointDescriptions"][point]["description"]
						except KeyError:
							group = "other"
							unit = None
							description = None
					graphs.setdefault(group, []).append({	"name": point,
										"src": "graphs/%s/%s" % (job, point),
										"unit": unit,
										"description": description})
				del(jobmetadata["points"])
				ret = {"version": 2, "graphs": graphs, "cview": cview, "tag": tag}
				ret.update(jobmetadata)
				return json.dumps(ret)

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
db = web.database(dbn=settings["dbtype"], host=settings["dbhost"], db=settings["dbname"], user=settings["dbuser"], password=settings["dbpass"])
app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()
