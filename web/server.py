# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle "BSD-style" open source license;
# the full text of that license is available in the COPYING file in the root of the repository
import urllib.error
import urllib.parse
import urllib.request
import hostlist
import web
import tarfile
import datetime
import os
CONFIG = "/etc/nwperf.conf"


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


settings = Settings(CONFIG)

db = web.database(dbn=settings["dbtype"], host=settings["dbhost"],
                  db=settings["dbname"], user=settings["dbuser"], passwd=settings["dbpass"])


def is_admin(user=None):
    if user == None:
        user = get_user()
    res = db.select(
        "user_table", where="name = $user and admin_level > '1'", vars={"user": user})
    return len(res) > 0


def get_user():
    try:
        # kerberos hack... Don't know if this is the right way
        return web.ctx.env["REMOTE_USER"].split("@")[0]
    except:
        return web.ctx.env["REMOTE_USER"]


def encode_datetime(obj):
    if isinstance(obj, datetime.datetime):
        return str(obj)
    elif isinstance(obj, datetime.timedelta):
        return str(obj)
    raise TypeError(repr(obj) + " is not JSON serializable")


class Graph(object):
    def GET(self, id, metric):
        res = db.select(settings["SlurmClusterName"]+"_job_table",
                        what="nodelist, time_start, time_end",
                        where="id_job = $id_job",
                        vars={"id_job": id})
        job = res[0]
        url = "%s/render" % (settings["GraphiteURL"])
        target = "%s{%s}.%s" % (settings["GraphitePrefix"],
                                ",".join(hostlist.expand_hostlist(
                                    job["nodelist"])),
                                metric
                                )
        if 'infiniband' not in metric:
            if 'cpu-' in metric or 'swap_io' in metric or metric.endswith('tx') or metric.endswith('rx') or metric.startswith('llite-') or metric.endswith('read') or metric.endswith('write'):
                target = "scaleToSeconds(derivative(%s),1)" % target
        data = urllib.parse.urlencode({
            "target": target,
            "from": datetime.datetime.fromtimestamp(job["time_start"]).strftime("%H:%M_%Y%m%d"),
            "until": datetime.datetime.fromtimestamp(job["time_end"]).strftime("%H:%M_%Y%m%d"),
            "format": "json",
            "maxDataPoints": 200})
        req = urllib.request.Request(url, data)
        ret = {}
        returned = urllib.request.urlopen(req).read()
        graphiteData = json.loads(returned)
        for metric in graphiteData:
            node = metric["target"].split(
                ".")[len(settings["GraphitePrefix"].split("."))-1]
            ret[node] = [[i[1] * 1000, i[0]] for i in metric["datapoints"]]
        return json.dumps(ret)


class GroupMembership(object):
    def GET(self, user):
        if user == "":
            user = get_user()
        res = ["admin"]
        return json.dumps(res)


class Jobs(object):
    def GET(self, job):
        input = web.input(q=None)
        tag = input.tag
        query = input.q
        if query != None:
            query = json.loads(query)
            if not is_admin():
                query.append(("User", get_user()))
            months = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                      "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
            fields = {"Start Date": "time_start", "End Date": "time_end", "Submit Date": "time_submit",
                      "Node Count": "nodes_alloc", "User": "user",
                      "Job Id": "id_job", "Account": "account"}
            where = ["%s_job_table.id_assoc = %s_assoc_table.id_assoc" %
                     ((settings["SlurmClusterName"],)*2), "time_end != 0"]
            runonnodes = []
            for queryItem in query:
                try:
                    column = fields[queryItem[0]]
                except:
                    pass
                if queryItem[0] in ("Start Date", "End Date", "Sumbit Date"):
                    if queryItem[1] not in ("<", ">"):
                        continue
                    if queryItem[0] == "End Date":
                        date = datetime.date(int(queryItem[4]), int(
                            months[queryItem[2]]), int(queryItem[3])).strftime("%s")
                        date = int(date) + 86400
                    else:
                        date = datetime.date(int(queryItem[4]), int(
                            months[queryItem[2]]), int(queryItem[3])).strftime("%s")
                    where.append("%s %s '%s'" % (column, queryItem[1], date))
                elif queryItem[0] == "Node Count":
                    if queryItem[1] not in ("<", ">", "==", "<=", ">="):
                        continue
                    if queryItem[1] == "==":
                        queryItem[1] = "="
                    where.append("%s %s %s" % (
                        column, queryItem[1], web.db.SQLParam(queryItem[2])))
                elif queryItem[0] in ("Job Id", "Account", "User"):
                    print(queryItem, web.db.SQLParam(queryItem[1]))
                    where.append("%s = '%s'" %
                                 (column, web.db.SQLParam(queryItem[1])))
                elif queryItem[0] == "Ran On Node":
                    runonnodes.append(queryItem[1])
            print(" and ".join(where))
            ret = db.select([settings["SlurmClusterName"]+"_job_table", settings["SlurmClusterName"]+"_assoc_table"],
                            what="id_job as id, user as User, id_job as JobID, id_job as jobid, account as Account, nodes_alloc as NumNodes, FROM_UNIXTIME(time_submit) as Submit, FROM_UNIXTIME(time_start) as Start, FROM_UNIXTIME(time_end) as End, TIMEDIFF(FROM_UNIXTIME(time_end), FROM_UNIXTIME(time_start)) as RunTime, nodelist",
                            where=" and ".join(where))
            print(" and ".join(where))
            for node in runonnodes:
                ret = [i for i in ret if node in hostlist.expand_hostlist(
                    i["nodelist"])]
            return json.dumps({"tag": tag, "jobs": tuple(ret)}, default=encode_datetime)
        else:
            job = int(job)
            res = db.select([settings["SlurmClusterName"]+"_job_table", settings["SlurmClusterName"]+'_assoc_table'],
                            where="id_job = $id_job and %s_job_table.id_assoc = %s_assoc_table.id_assoc" % (
                                settings["SlurmClusterName"], settings["SlurmClusterName"]),
                            vars={"id_job": job})
            job = tuple(res)[0]
            metrics = set()
            for level in range(4):
                url = "%s/metrics/expand?query=%s%s%s&leavesOnly=1" % (
                    settings["GraphiteURL"],
                    settings["GraphitePrefix"],
                    hostlist.expand_hostlist(job["nodelist"])[0],
                    ".*"*level)
                res = urllib.request.urlopen(url).read()
                res = json.loads(res)
                metrics.update([".".join(i.split(".")[3:])
                               for i in res["results"]])
            graphs = {}
            for metric in metrics:
                try:
                    group = graphs[metric.split(".")[0]]
                except KeyError:
                    group = graphs[metric.split(".")[0]] = []
                group.append(
                    {"src": "graphs/%s/%s" % (job["id_job"], metric), "description": "", "name": metric, "unit": ""})
            return json.dumps({"version": 2,
                               "cview": False,
                               "Account": job["account"],
                               "CPUTime": "",
                               "Elapsed": "",
                               "End": datetime.datetime.fromtimestamp(job["time_end"]).isoformat(),
                               "ExitCode": job["exit_code"],
                               "Gid": job["user"],
                               "JobID": job["id_job"],
                               "JobName": job["job_name"],
                               "Graphs": graphs,
                               "NodeList": job["nodelist"],
                               "NumNodes": len(hostlist.expand_hostlist(job["nodelist"])),
                               "RunTime": job["time_end"] - job["time_start"],
                               "Start": datetime.datetime.fromtimestamp(job["time_start"]).isoformat(),
                               "State": job["state"],
                               "Submit": job["time_submit"],
                               "User": job["user"],
                               "cluster": settings["SlurmClusterName"],
                               "Nodes": hostlist.expand_hostlist(job["nodelist"]),
                               "tag": tag})


class Users(object):
    def GET(self):
        if is_admin():
            res = db.select("user_table", what="distinct name as user")
            return json.dumps([i["user"] for i in res])
        else:
            return json.dumps([get_user()])


urls = (
    '/cview/(\d+)', 'Cview',
    '/graphs/(\d+)/(.*)', 'Graph',
    '/groupMembership/(.*)', 'GroupMembership',
    '/jobs/(.*)', 'Jobs',
    '/users/', 'Users'
)

app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()
