#!/usr/bin/python
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import numpy
import time
import struct
from nwperf import nwperfceph
import nwperf
import hostlist
import web
import csv
import StringIO
import traceback
clusters = {}

def getRDS(cluster):
	try:
		return clusters[cluster]
	except:
		#sys.stderr.write("Connect to rados\n")
		rds = nwperfceph.RadosDataStore("/etc/ceph/ceph.conf",cluster,"nwperf")
		clusters[cluster]=rds
		return rds

class ClusterCView:
	def GET(self,cluster,request):
		cluster=str(cluster)
		request=str(request)

		msg="Request did not match"
		hosts=[]
		try: 
			if request == "index":
				return getRDS(cluster).getIndex()
			if request.endswith('.desc'):
				return getRDS(cluster).getDescription(request[:-5])

			t=int(time.time())
			e=t-(128*60)
			if request.endswith('.rate'):
				return getRDS(cluster).getRate(t,request[:-5])

			if request.endswith('.ytick'):
				data=''
				for i in getRDS(cluster).getYTicks(e,t):
					data += struct.pack("32s",i)
				return data

			if request.endswith('.data'):
				return getRDS(cluster).getDataSlice(e,t,request[:-5]).tostring()
			if request == 'xtick':
				hosts = getRDS(cluster).getXTicks()
				data=''
				for i in hosts:
					data+=struct.pack("32s",i)
				return data
		except Exception,msg:
			sys.stderr.write("Error getting data:"+str(msg)+":"+request)

		return [msg,request,cluster,hosts]

class JobCView:
	def GET(self,cluster,jid,request):
		#get rid of unicode
		jid=str(jid)
		cluster=str(cluster)
		request=str(request)
		msg="Request did not match"
		hosts=[]
		try: 
			if request == "index":
				return getRDS(cluster).getIndex()
			if request.endswith('.desc'):
				return getRDS(cluster).getDescription(request[:-5])
		
			t=int(time.time())
			if request.endswith('.rate'):
				return getRDS(cluster).getRate(t,request[:-5])

			job = nwperf.getJobInfo(jid,cluster,"tcp://nwperf-ns:6967")
			s,e = nwperf.getJobTimes(job,0)

			if request.endswith('.ytick'):
				data=''
				for i in getRDS(cluster).getYTicks(s,e):
					data += struct.pack("32s",i)
				return data

			hosts = hostlist.expand_hostlist(job["NodeList"],e)
			if request.endswith('.data'):
				points = getRDS(cluster).getDataSlice(s,e,request[:-5],hosts)
				return points.tostring()
			if request == 'xtick':
				data=''
				for i in hosts:
					data+=struct.pack("32s",i)
				return data
			
			if request.endswith(".csv"):
				sio = StringIO.StringIO()
				c = csv.writer(sio)
				
				c.writerow(["Host"]+getRDS(cluster).getYTicks(s,e))
				points = getRDS(cluster).getDataSlice(s,e,request[:-4],hosts)	
				for x in xrange(0,points.shape[0]):
					c.writerow([hosts[x]]+[str(i) for i in points[x]])

				data = sio.getvalue()
				sio.close()
				return data
		except Exception,msg:
			sys.stderr.write("Error getting data:"+traceback.format_exc()+":"+request)

		return [msg,request,job,jid,cluster,hosts]

class Broken:
	def GET(self,arg):
		return ["This is Broken:"+arg]





urls = (
	'/([^/]*)/job/(\d+)/(.*)','JobCView',
	'/([^/]*)/(.*)','ClusterCView',
	'/cluster/([^/]*)/(.*)','ClusterCView',
	'/(.*)','Broken',
	)
app = web.application(urls,globals(), autoreload=False)
application = app.wsgifunc()


if __name__ == "__main__":
	from wsgiref.simple_server import make_server

	httpd = make_server('', 8042, application)
	print "Serving on port 8042..."
	httpd.serve_forever()
