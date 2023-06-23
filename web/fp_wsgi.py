#!/usr/bin/python
from calendar import timegm
import simplejson as json
import math
import mimetypes
import traceback
import io
import csv
import web
import hostlist
import nwperf
from nwperf import nwperfceph
import struct
import time
import numpy
import os
import os.path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
clusters = {}
staticPath = "web/webgl"
web.config.debug = False


def cors():
    web.header('Access-Control-Allow-Headers', 'accept, content-type')
    web.header('Access-Control-Allow-Methods', 'POST')
    web.header('Access-Control-Allow-Origin', '*')


def getRDS(cluster):
    try:
        return clusters[cluster]
    except:
        #sys.stderr.write("Connect to rados\n")
        rds = nwperfceph.RadosDataStore(
            "/etc/ceph/ceph.conf", cluster, "nwperf")
        clusters[cluster] = rds
        return rds


class ClusterCView:
    def GET(self, cluster, request):
        cluster = str(cluster)
        request = str(request)

        msg = "Request did not match"
        hosts = []
        try:
            if request == "index":
                return getRDS(cluster).getIndex()
            if request.endswith('.desc'):
                return getRDS(cluster).getDescription(request[:-5])

            t = int(time.time())
            e = t-(128*60)
            if request.endswith('.rate'):
                return getRDS(cluster).getRate(t, request[:-5])

            if request.endswith('.ytick'):
                data = ''
                for i in getRDS(cluster).getYTicks(e, t):
                    data += struct.pack("32s", i)
                return data

            if request.endswith('.data'):
                return getRDS(cluster).getDataSlice(e, t, request[:-5]).tostring()
            if request == 'xtick':
                hosts = getRDS(cluster).getXTicks()
                data = ''
                for i in hosts:
                    data += struct.pack("32s", i)
                return data
        except Exception as msg:
            sys.stderr.write("Error getting data:"+str(msg)+":"+request)

        return [msg, request, cluster, hosts]


class JobCView:
    def GET(self, cluster, jid, request):
        # get rid of unicode
        jid = str(jid)
        cluster = str(cluster)
        request = str(request)
        msg = "Request did not match"
        hosts = []
        try:
            if request == "index":
                return getRDS(cluster).getIndex()
            if request.endswith('.desc'):
                return getRDS(cluster).getDescription(request[:-5])

            t = int(time.time())
            if request.endswith('.rate'):
                return getRDS(cluster).getRate(t, request[:-5])

            job = nwperf.getJobInfo(jid, cluster, "tcp://nwperf-ns:6967")
            s, e = nwperf.getJobTimes(job, 0)

            if request.endswith('.ytick'):
                data = ''
                for i in getRDS(cluster).getYTicks(s, e):
                    data += struct.pack("32s", i)
                return data

            hosts = hostlist.expand_hostlist(job["NodeList"], e)
            if request.endswith('.data'):
                points = getRDS(cluster).getDataSlice(
                    s, e, request[:-5], hosts)
                return points.tostring()
            if request == 'xtick':
                data = ''
                for i in hosts:
                    data += struct.pack("32s", i)
                return data

            if request.endswith(".csv"):
                sio = io.StringIO()
                c = csv.writer(sio)

                c.writerow(["Host"]+getRDS(cluster).getYTicks(s, e))
                points = getRDS(cluster).getDataSlice(
                    s, e, request[:-4], hosts)
                for x in range(0, points.shape[0]):
                    c.writerow([hosts[x]]+[str(i) for i in points[x]])

                data = sio.getvalue()
                sio.close()
                return data
        except Exception as msg:
            sys.stderr.write("Error getting data:" +
                             traceback.format_exc()+":"+request)

        return [msg, request, job, jid, cluster, hosts]


class StaticFile:
    def GET(self, arg):
        path = os.path.normpath(staticPath+os.sep+arg)
        if path.startswith(staticPath) and os.path.exists(path):
            f = open(path, 'rb')
            data = f.read()
            f.close()
            return data
        else:
            return "This is Broken:", arg, path, path.startswith(staticPath), os.path.exists(path)


class Health:
    def GET(self):
        return "<html><h1>Running</h1></html>"


class Broken:
    def GET(self, arg):
        print("Broken")
        return web.notfound("This is Broken:"+arg)


class Test:
    def GET(self, arg):
        try:
            rds = getRDS(arg)
        except IndexError as msg:
            print("error:", arg, "not found:", msg)
            raise web.notfound()
        cors()
        return "Test of The Service:"+arg


class Search:
    def OPTIONS(self, arg):
        cors()
        return "Search Options Called"

    def POST(self, arg):
        cors()
        print(web.data())
        rds = getRDS(arg)
        index = rds.getIndex().split('\n')
        return json.dumps(index)


class Query:
    def OPTIONS(self, arg):
        cors()
        return "Query Options Called"

    def POST(self, arg):
        cors()
        print(web.data())
        params = json.loads(web.data())
        rds = getRDS(arg)
        maxlength = params['maxDataPoints']

        # figure out time ranges.
        start = timegm(time.strptime(
            params['range']['from'], "%Y-%m-%dT%H:%M:%S.%fZ"))
        end = timegm(time.strptime(
            params['range']['to'], "%Y-%m-%dT%H:%M:%S.%fZ"))
        s = nwperfceph.prevmin(start)/60
        e = nwperfceph.prevmin(end)/60
        print(s, e)

        series = []
        for target in params['targets']:
            # print "Target:",target
            data = rds.getDataSlice(start, end, target['target'])
            length = len(data[0])
            print(length)

            if length > maxlength:
                sumlength = length/maxlength
                leftover = -(length % maxlength)
            else:
                sumlength = 1
                leftover = length
            interval = 60000*sumlength
            print("len", length, sumlength, leftover)
            for row in rds.getXTicks():
                tgt = {'target': row+":"+target['target']}
                index = rds.hostindex(row)
                line = data[index]

                line = numpy.mean(
                    line[:leftover].reshape(-1, sumlength), axis=1)
                if index == 0:
                    print("newlen", len(line))
                if index == 0:
                    print("DERP", e*60000, s*60000, -interval)
                dp = list(zip(line.tolist(), list(
                    range(e*60000, s*60000, -interval))))

                tgt['datapoints'] = dp
                series.append(tgt)
        return json.dumps(series)


class Raw:
    def GET(self, cluster, obj):
        rds = getRDS(cluster)
        chunk = 1024*1024
        stat = rds.ioctx.stat(obj)
        pos = 0
        while pos < stat[0]:
            data = rds.ioctx.read(obj, length=chunk, offset=pos)
            yield data
            pos += chunk


urls = (
    '/cluster/([^/]*)/(.*)', 'ClusterCView',
    '/static/(.*)', 'StaticFile',
    '/([^/]*)/search', 'Search',
    '/([^/]*)/query', 'Query',
    '/([^/]*)/raw/(.*)', 'Raw',
    # '/([^/]*)/?','Test',
    '/([^/]*)/job/(\d+)/(.*)', 'JobCView',
    '/([^/]*)/(.*)', 'ClusterCView',
    '/health', 'Health',
    '/(.*)', 'Broken',
)
mimetypes.init()
app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()


if __name__ == "__main__":
    from wsgiref.simple_server import make_server, WSGIServer
    from socketserver import ThreadingMixIn

    class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
        pass
    httpd = make_server('', 4050, application, ThreadingWSGIServer)
    print("Serving on port 4050...")
    httpd.serve_forever()
