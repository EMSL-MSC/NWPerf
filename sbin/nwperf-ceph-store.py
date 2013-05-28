#!/usr/bin/env python

import zmq
import time
import sys
#sys.path.append("/home/efelix/cephbuild/lib/python2.6/site-packages/")
import rados
import struct
import simplejson as json
import nwperf
from nwperf import nwperfceph
from operator import itemgetter


seenobjects={}
hostsizes={}

def processWork(r_ioctx,worklist):
	global seenobjects
	write_count=0
	start=time.time()
	print "Work",start,sum([len(i) for i in worklist.values()])

	for object in worklist.keys():
		cur_offset=-0xEF
		start_offset=0
		data=''
		thelist=worklist[object]
		#print "Work",time.time(),len(thelist),object
		thelist.sort(key=itemgetter(0))

		if not seenobjects.has_key(object):
			daysize=1440*hostsizes[object.split("/")[0]]
			r_ioctx.trunc(object,daysize*4)
			seenobjects[object]=1

		for item in thelist:
			offset,val = item
			#print item

			#case: new value fits after current stream
			if cur_offset+4 == offset: 
				data += struct.pack("<f",val)
				cur_offset = offset

			#case: new value is somewhere else in stream
			else:
				#flush old data
				#print "write1", object,start_offset,len(data)
				r_ioctx.aio_write(object,data,start_offset)
				write_count+=1

				#setup for new one
				start_offset = offset
				cur_offset=offset
				data = struct.pack("<f",val)

		#flush final line
		#print "write2", cur_object,start_offset,len(data)
		r_ioctx.aio_write(object,data,start_offset)
		write_count+=1

	end=time.time()
	print "Done",end,sum([len(i) for i in worklist.values()]),write_count
	return end-start

def connectZMQ(nsurl,points):
	#zmq setup
	z_ctx = zmq.Context()

	z_sock_ns = z_ctx.socket(zmq.REQ)
	z_sock_ns.connect(nsurl)

	urls=[]
	for name in points:
		z_sock_ns.send_multipart(("1","getService",name))
		urls+=z_sock_ns.recv_multipart()
	print urls

	z_sock_data = z_ctx.socket(zmq.SUB)
	z_sock_data.setsockopt(zmq.SUBSCRIBE, "")
	z_sock_data.setsockopt(zmq.RCVBUF, 4194304)
	for url in urls[::2]:
		if url != 'ERROR':
			z_sock_data.connect(url)

	z_poll = zmq.core.Poller()
	z_poll.register(z_sock_data,zmq.POLLIN)

	return z_sock_data,z_poll

def main(zmqns,cephconfig,cluster):
	objectinfo={}

	#rados setup
	r_cluster = rados.Rados(conffile=cephconfig)
	r_cluster.connect()
	r_ioctx = r_cluster.open_ioctx(cluster+".points")
	rds=nwperfceph.RadosDataStore(cephconfig,cluster)

	data = r_ioctx.read("hostorder",65535)
	#hosts will have all hosts, even if the timestamp in hostorder.sizelog shows smaller.
	hosts=data.split("\n")[:-1]
	#hostcount=len(hosts)
	#daysize=hostcount*1440
	#print hostcount,daysize
	id=0
	hostorder={}
	for host in hosts:
		hostorder[host]=id
		id+=1
	try:
		data = r_ioctx.read("pointindex",65535)
		pointlist = data.split("\n")[:-1]
	except rados.ObjectNotFound:
		pointlist=[]


	z_sock_data,z_poll = connectZMQ(zmqns,(cluster+".allpoints",))

	lastdata=0;
	worktime=1
	try:
		work={}
		olddata=False
		while True:
			res = z_poll.poll(1000) #returns # of events ready
			if res:
				old=time.time()-3600
				header,data = z_sock_data.recv_multipart()
				if header == 'Point':
					try:
						data = json.loads(data)
						#print data
						# sample: {'host': 'cu01n101', 'time': '1343863450', 'val': '52', 'unit': 'percent', 'pointname': 'cputotals.user'}
						secs = int(data['time'])
						if secs < old:
							olddata=data
							continue
						val = float(data['val'])
						daystring = time.strftime("%Y-%m-%d",time.gmtime(secs))
						object = daystring+"/"+data['pointname']
						try:
							location=hostorder[data['host'].partition(".")[0]] 
						except KeyError:
							#print "bad host",data
							continue
						try:
							hostcount=hostsizes[daystring]
						except KeyError:
							hostcount=rds.getHostCount(secs)
							print "hostcount",secs,hostcount
							hostsizes[daystring]=hostcount
						minute = secs%86400/60
						offset = 4*(minute*hostcount+location)
						#print object, minute, location, offset
						if not data['pointname'] in pointlist:
							print "adding",data['pointname']
							r_ioctx.aio_append('pointindex',data['pointname']+"\n")
							pointlist.append(data['pointname'])
						try:
							work[object].append((offset,val))
						except KeyError:
							work[object]=[(offset,val)]
							r_ioctx.set_xattr(object, 'unit', data['unit'])
					except ValueError,msg:
						print "Error consuming a data point:",msg
						print data
				else:
					#print header
					pass
			else:
				if sum([len(i) for i in work.values()]):
					#dump old keys
					for key in work.keys():
						if not work[key]:
							del work[key]
					worktime=processWork(r_ioctx,work)	
					lastdata = time.time()

				for key in work.keys():
						work[key]=[]
				#print len(work.keys())
				if time.time()-lastdata > 120 or worktime > 120:
					print "Reconnecting to zmq"
					z_sock_data,z_poll = connectZMQ(zmqns,(cluster+".allpoints",))
					#wait at least 30 seconds for next try
					lastdata = time.time()-90
				if olddata:
					print "Old Data Seen, sample: ",olddata
					olddata=False
					
	except KeyboardInterrupt:
		pass
	except zmq.ZMQError,msg:
		print "ZMQ error, exiting:",msg
			
	r_ioctx.close()
	r_cluster.shutdown()

if __name__ == "__main__":
	parser = nwperf.defaultServerOptionParser()
	parser.add_option("-S","--name-server",dest="nameserver",type="string",help="The ZMQ URL of the nameserver to register with",default="tcp://nwperf-ns:6967")
	parser.add_option("-c","--cluster",dest="cluster",type="string",help="The cluster prefix to publish as",default=None)
	parser.add_option("-f","--ceph-config",dest="cephconfig",type="string",help="Location of the ceph config file",default="/etc/ceph/ceph.conf")

	options,args = nwperf.parseServerOptions()

	if not options.cluster:
		parser.error("No Cluster Specified")

	main(options.nameserver,options.cephconfig,options.cluster) 

