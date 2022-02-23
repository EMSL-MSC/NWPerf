#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle "BSD-style" open source license;
# the full text of that license is available in the COPYING file in the root of the repository
#
# Author: Evan J. Felix
#

import zmq
import time
import sys
import traceback
import simplejson as json
import nwperf
import nwperf.msclog
from nwperf import nwperfceph

WORK_CHUNK_SIZE = 10000
PROCESS_POOL_COUNT = 16
MINUTES_TO_MANAGE = 10
FLUSH_INTERVAL = 30

TEST = 'aggregation-cpu-average/cpu-user'
TESTMODE = 0

_log = nwperf.msclog.getLogger("root.ncs")
nwperf.msclog.logToError()
nwperf.msclog.setLevel(nwperf.msclog.INFO)


class Metric:
    """
            manages a set of recent data arrays, assuming this is the only process managing
            rados datasets, its safe to write the last few minutes without worrying about
            others overwriting the data.
    """

    def __init__(self, objectname, rds, queue):
        self.q = queue
        self.rds = rds
        self.name = objectname
        self.daemon = True
        self.curdata = {}
        nowmin = int(time.time())/60
        for i in range(nowmin, nowmin-MINUTES_TO_MANAGE, -1):
            self.curdata[i] = {'data': self.getDataRow(i*60), 'dirty': False}

    def getDataRow(self, thetime):
        try:
            row = self.rds.getDataRow(thetime, self.name)
        except KeyError:
            self.rds.createObject(thetime, self.name)
            row = self.rds.getDataRow(thetime, self.name)
        return row

    def flushAndEvict(self):
        evict = None
        for k, v in self.curdata.items():
            if v['dirty']:
                v['dirty'] = False
                if TESTMODE:
                    print(v['data'])
                self.rds.putDataRow(k*60, self.name, v['data'])
            if k < int(time.time())/60-MINUTES_TO_MANAGE:
                # print "evict",k
                evict = k
        if evict:
            del self.curdata[evict]

    def addOne(self, data):
        hostindex, secs, val = data
        minute = secs/60
        #_log.debug("%s:Processing data: %d %d %d %f",self.name,hostindex,secs,minute,val)
        try:
            self.curdata[minute]["dirty"] = True
        except KeyError:
            # print "create new"
            self.curdata[minute] = {
                'data': self.getDataRow(minute*60), 'dirty': True}
            # print "create new done"
        self.curdata[minute]["data"][hostindex] = val


class DataManager:
    def __init__(self, zmqns, cephconfig, cluster, cephid):
        self.zmqns = zmqns
        self.cephconfig = cephconfig
        self.cluster = cluster
        self.cephid = cephid
        self.metrics = {}
        self.initCeph()
        self.createMetrics()
        self.resetZMQ()

    def resetZMQ(self):
        _log.info("reconnecting to zmq: %s %s",
                  self.zmqns, (self.cluster+".allpoints",))
        self.z_sock, self.z_poll = connectZMQ(
            self.zmqns, (self.cluster+".allpoints",))

    def initCeph(self):
        self.rds = nwperfceph.RadosDataStore(
            self.cephconfig, self.cluster, self.cephid)
        self.hostlist = self.rds.hostlist()
        data = self.rds.getIndex()
        self.pointlist = data.split("\n")[:-1]

    def createMetrics(self):
        if TESTMODE:
            self.metrics[TEST] = Metric(
                TEST, self.rds, self.objectqueues[TEST])
        else:
            for k in self.pointlist:
                self.metrics[k] = Metric(k, self.rds, None)

    def run(self):
        currentdata = []
        nextcheck = time.time()+60
        while True:
            res = self.z_poll.poll(1000)  # returns # of events ready
            if res:
                header, data = self.z_sock.recv_multipart()
                if header == 'Point':
                    currentdata.append(data)
                else:
                    _log.warn("Foreign header: %s", header)
            else:
                # idle work here.
                # have we seen data lately, reset stuff
                if time.time() > nextcheck:
                    self.resetZMQ()
                    nextcheck = time.time()+30

            if len(currentdata) >= WORK_CHUNK_SIZE or (not res and currentdata):
                self.convertWorkToMetics(currentdata)
                currentdata = []
                for o in self.metrics.values():
                    o.flushAndEvict()
                nextcheck = time.time()+120

    def convertWorkToMetics(self, work):
        old = time.time()-MINUTES_TO_MANAGE*60
        #_log.debug("converting data block of %d size:",len(work))
        l = []
        try:
            for datum in work:
                # sample: {'host': 'cu01n101', 'time': '1343863450', 'val': '52', 'unit': 'percent', 'pointname': 'cpu-14/cpu-user'}
                data = json.loads(datum)
                # print data
                secs = int(float(data['time']))
                if secs < old:
                    #_log.debug("Old data seen:%s %d < %d",data,secs,old)
                    print(".", end=' ')
                    continue
                if not data["host"] in self.hostlist:
                    continue
                val = float(data['val'])
                # if data["pointname"] == TEST:
                l.append(
                    (data["pointname"], (self.hostlist.index(data["host"]), secs, val)))
                # if data["pointname"] == TEST:
                #	print data
            for k, v in l:
                # fixme, can we do this in the above loop?
                if k in self.metrics:
                    self.metrics[k].addOne(v)
                else:
                    _log.debug("missing metric key: %s %s", k, v)
            #_log.debug("done converting data block of %d size:",len(work))
        except Exception as e:
            print(traceback.print_exception(type(e), e, sys.exc_info()[2]))

    def terminate(self):
        pass


def connectZMQ(nsurl, points):
    # zmq setup
    z_ctx = zmq.Context()

    z_sock_ns = z_ctx.socket(zmq.REQ)
    z_sock_ns.connect(nsurl)

    urls = []
    for name in points:
        z_sock_ns.send_multipart(("1", "getService", name))
        urls += z_sock_ns.recv_multipart()
    print(name, urls)

    z_sock_data = z_ctx.socket(zmq.SUB)
    z_sock_data.setsockopt(zmq.SUBSCRIBE, "")
    z_sock_data.setsockopt(zmq.RCVBUF, 4194304)
    for url in urls[::2]:
        if url != 'ERROR':
            z_sock_data.connect(url)

    z_poll = zmq.Poller()
    z_poll.register(z_sock_data, zmq.POLLIN)

    return z_sock_data, z_poll


if __name__ == "__main__":
    parser = nwperf.defaultServerOptionParser()
    parser.add_option("-S", "--name-server", dest="nameserver", type="string",
                      help="The ZMQ URL of the nameserver to register with", default="tcp://nwperf-ns:6967")
    parser.add_option("-c", "--cluster", dest="cluster", type="string",
                      help="The cluster prefix to publish as", default=None)
    parser.add_option("-f", "--ceph-config", dest="cephconfig", type="string",
                      help="Location of the ceph config file", default="/etc/ceph/ceph.conf")
    parser.add_option("-i", "--ceph-id", dest="cephid",
                      type="string", help="Ceph client id")

    options, args = nwperf.parseServerOptions()

    if not options.cluster:
        parser.error("No Cluster Specified")
    try:
        dm = DataManager(options.nameserver, options.cephconfig,
                         options.cluster, options.cephid)
        dm.run()
    except KeyboardInterrupt:
        dm.terminate()
