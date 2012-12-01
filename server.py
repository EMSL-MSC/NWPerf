dbtype = "postgres"
dbhost = "fishladder.emsl.pnl.gov"
dbname = "nwperf"
dbuser = "guppy"
dbpass = "GuPpY"
flotgraphsdir = "/var/www/nwperf-graphs/flot-graphs/newgraphs"
graphsdir = "/var/www/nwperf-graphs/"
tempdir = "/tmp/"
cviewdir = "/var/www/nwperf-graphs/cview/jobs/"

import os
import datetime
import tarfile
import web
try:
	import simplejson as json
except:
	import json

db = web.database(dbn=dbtype, host=dbhost, db=dbname, user=dbuser, password=dbpass)

def is_admin(user = None):
	if user == None:
		user = get_user()
	res = db.select("usergroups", where="nwperf_user = $user and nwperf_group = 'admin'", vars={"user": user})
	return len(res) > 0

def get_user():
	try:
		#kerberos hack... Don't know if this is the right way
		return web.ctx.env["REMOTE_USER"].split("@")[0]
	except:
		return web.ctx.env["REMOTE_USER"]


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

		res = db.select("moab_job_details", where="moab_job_details.user = $user and jobs_id = $id", vars={"user": user, "id": id})
		jobOwner = len(res) > 0

                file = os.path.join(cviewdir, str(id%100), str(id/100%100), "%d.tar.gz" %id)
                cviewAvail = os.path.exists(file)

		ret = str(web.ctx.env)
		if (jobOwner or is_admin(user)) and cviewAvail:
			web.header('Content-type', 'application/x-cviewall')
			web.header('Content-Disposition', 'attachment; filename="%d.cviewall"' % id)
			ret  = '{\n'
			ret += '\turl = "http://nwperf.emsl.pnl.gov/jobs/%d/";\n' % id
			ret += '\tmetrics = ("cputotals.user", "meminfo.used");\n'
			ret += '\tdataUpdateInterval = 0.0;\n'
			ret += '}\n'
		return ret

class Graph(object):
	def GET(self, id, metric):
		pointArchiveDir = os.path.join(tempdir,"flot",id)
		try:
			return open(os.path.join(pointArchiveDir,"%s.flot" % metric)).read()
		except IOError:
			import phpserialize
			id = int(id)
			pointsDir = os.path.join(graphsdir, str(id%100), str(id/100%100), str(id))
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
		res = db.select("usergroups", what="nwperf_group", where="nwperf_user = $user", vars={"user": user})
		#return json.dumps([])
		return json.dumps([i["nwperf_group"] for i in res])

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
			fields = {	"Start Date": "start_time", "End Date": "end_time", "Submit Date": "submit_time",
					"Dispatch Date": "dispatch_time", "Node Count": "num_nodes_allocated", "User": "moab_job_details.user",
					"Job Id": "jobs.job_id", "Account": "account"}
			where = ["jobs.id = moab_job_details.jobs_id"]
			for queryItem in query:
				try:
					queryItem[0] = fields[queryItem[0]]
				except:
					pass
				if queryItem[0] in ("start_time", "end_time", "submit_time", "dispatch_time"):
					if queryItem[1] not in  ("<", ">"):
						continue
					if queryItem[0] == "end_time":
						date = web.db.SQLParam("%s-%s-%s 23:59:59" % (queryItem[4], months[queryItem[2]], queryItem[3]))
					else:
						date = web.db.SQLParam("%s-%s-%s 00:00:00" % (queryItem[4], months[queryItem[2]], queryItem[3]))
					where.append(	"%s %s '%s'" % ( queryItem[0], queryItem[1], date))
				elif queryItem[0] ==  "num_nodes_allocated":
					if queryItem[1] not in  ("<", ">", "==", "<=", ">="):
						continue
					where.append("%s %s %s" % (queryItem[0], queryItem[1], web.db.SQLParam(queryItem[2])))
				elif queryItem[0] in ("jobs.job_id", "account", "moab_job_details.user"):
					where.append("%s = '%s'" % (queryItem[0], web.db.SQLParam(queryItem[1])))
				elif queryItem[0] == "Ran On Node":
					where.append("moab_job_details.jobs_id in (select job_id from host_jobs, hosts where host_jobs.host_id = hosts.id and hosts.host_name = '%s')" % web.db.SQLParam(queryItem[1]))
			ret = db.select(["moab_job_details", "jobs"],
					what="jobs.job_id as id, moab_job_details.user as user, 'chinook-'||job_id||'-'||extract(epoch from start_time) as jobId, account, num_nodes_allocated as numNodes, submit_time as submitTime, start_time as startTime, end_time as endTime, end_time-start_time as runTime",
					where=" and ".join(where))
			return json.dumps({"tag": tag, "jobs": tuple(ret)}, default=encode_datetime)
	
		else:
			(cluster, jobnum, starttime) = job.split("-")
			jobnum = int(jobnum)
			starttime = int(starttime)
			if ".." in cluster:
				return json.dumps({"error": "Invalid job id"})
			#file = os.path.join(cviewdir, str(job%100), str(job/100%100), "%d.tar.gz" % job)
			#cview = {True: "cview/%s" % job, False: False}[os.path.exists(file)]
			cview = False

			pointsArchive = os.path.join(flotgraphsdir, str(jobnum%100), str(jobnum/100%100), "%s.tar.bz2" % job)
			if not os.path.exists(pointsArchive): 
				ret = db.select(["jobs", "moab_job_details"],
						what="jobs.id as id",
						where="jobs.id = moab_job_details.jobs_id and job_id = $id and start_time = TIMESTAMP WITH TIME ZONE 'epoch' + $starttime * INTERVAL '1 second'",
						vars={"id": jobnum, "starttime": starttime})
				job = ret["id"]
				pointsDir = os.path.join(graphsdir, str(job%100), str(job/100%100), str(job))
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
			else:
				graphs = {}
				pointsDir = os.path.join(tempdir, "flot")
				if not os.path.exists(pointsDir):
					os.mkdir(pointsDir)
				pointsDir = os.path.join(pointsDir,str(job))
				if not os.path.exists(pointsDir):
					tar = tarfile.open(pointsArchive)
					tar.extractall(pointsDir)
				try:
					metadata = json.load(open(os.path.join(pointsDir, "metadata")))
				except:
					return json.dumps({"error": "Error reading job metadata", "tag": tag})
				for point in metadata["points"]:
					res = db.select("point_descriptions pd, point_groups pg",
							what="point_description as description, name as group, pd.units as units",
							where="pd.point_groups_id = pg.id and point_name = $point",
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
						
					graphs.setdefault(group, []).append({	"name": point,
										"src": "graphs/%s/%s" % (job, point),
										"unit": unit,
										"description": description})
				del(metadata["points"])
				ret = {"version": 2, "graphs": graphs, "cview": cview, "tag": tag}
				ret.update(metadata)
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
    '/jobs/(.*)', 'Jobs',
    '/users/', 'Users'
)

app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()
