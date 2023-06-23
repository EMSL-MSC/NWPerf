#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle "BSD-style" open source license;
# the full text of that license is available in the COPYING file in the root of the repository

import rados
import numpy
import time
from nwperf import Settings
import re
_collectdre = re.compile("^[^-]*-?.*/([^-]*)-.*$")

_settings = Settings("/etc/nwperf.conf")
_typedb = _settings["collectdtypes"]

DAY = 86400
DAYMIN = DAY/60


def prevmin(seconds):
    return int(seconds/60.0)*60


class RadosDataStore:
    def __init__(self, cephconfig, cluster, myid=None):
        self.cluster = cluster
        self.id = myid
        self.r_cluster = rados.Rados(conffile=cephconfig, rados_id=myid)
        self.r_cluster.connect()
        self.ioctx = self.r_cluster.open_ioctx(cluster+".points")
        # host order should not change
        self.hosts = self.ioctx.read("hostorder", 65535).split("\n")[:-1]
        self.index = self.getIndex().split("\n")
        self.hostcachetime = 0
        self.hostcount = -1

    def __del__(self):
        self.ioctx.close()
        self.r_cluster.shutdown()

    def hostlist(self):
        return self.hosts

    def hostindex(self, o):
        # silly hack to deal with pic and adding .local to everything
        try:
            return self.hosts.index(o)
        except:
            # return self.hosts.index(o+".local")
            print("missing host:"+o)
            return 0  # crappy hack for now.. deal with missing hosts somehow?

    def getIndex(self):
        data = self.ioctx.read('pointindex')
        return data

    def getXTicks(self, time=time.time()):
        return self.hosts[:self.getHostCount(time)]

    def getDescription(self, key):
        data = self.ioctx.read("pointdesc", 1024*1024)
        lines = data.split("\n")[:-1]
        for line in lines:
            k, desc = line.split(":", 1)
            if k == key:
                return desc
        return "No Description in Ceph Database"

    def getRate(self, reftime, key):
        cdm = _collectdre.match(key)
        if cdm:
            try:
                unit = _typedb[cdm.group(1)]['unit']
            except:
                unit = "No unit in nwperf.conf:"+key
        else:
            try:
                # look backwards a little in case we are on the day boundary, and the object is not there yet.
                daystr = time.strftime("%Y-%m-%d", time.gmtime(reftime-300))
                unit = self.ioctx.get_xattr(daystr+"/"+key, "unit")
            except rados.ObjectNotFound:
                unit = "Error Getting Rate Unit:"+daystr+" "+key
            except rados.NoData:
                unit = "Error Getting Rate Unit:"+daystr+" "+key
        return unit

    def getDataRow(self, thetime, key):
        """return a one minute time slice from the cluster"""
        hostcount = self.getHostCount(thetime)
        daystr = time.strftime("%Y-%m-%d", time.gmtime(thetime))
        themin = thetime/60

        # print daystr+"/"+key,hostcount*4,(themin%1440)*hostcount*4
        try:
            mindata = self.ioctx.read(
                daystr+"/"+key, length=hostcount*4, offset=(themin % 1440)*hostcount*4)
            minarray = numpy.frombuffer(mindata, dtype='f4')
        except rados.ObjectNotFound:
            raise KeyError

        # print minarray
        return minarray.copy()

    def createObject(self, thetime, key):
        """add a new object for the specified date, setting unit, and adding to point index if needed"""
        hostcount = self.getHostCount(thetime)
        daystr = time.strftime("%Y-%m-%d", time.gmtime(thetime))
        # print "createObject",thetime,key,daystr,daystr+"/"+key
        daysize = 1440*hostcount
        self.ioctx.write_full(
            daystr+"/"+key, numpy.zeros((daysize*4,)).tostring())
        if not key in self.index:
            print("adding to pointindex: ", key)
            self.ioctx.aio_append('pointindex', key+"\n")
            self.index.append(key)

    def putDataRow(self, thetime, key, data):
        hostcount = self.getHostCount(thetime)
        daystr = time.strftime("%Y-%m-%d", time.gmtime(thetime))
        themin = thetime/60
        # print "putDataRow",thetime,daystr,key
        self.ioctx.aio_write(daystr+"/"+key, data.tostring(),
                             (themin % 1440)*hostcount*4)

    def getDataSlice(self, start, end, key, hostlist=None):
        """return a dataslice from the cluster"""
        # print "getDS:",start,end,key
        start = prevmin(start)
        end = prevmin(end)
        hostcount = max(self.getHostCount(start), self.getHostCount(end))
        # print "hostcount",hostcount

        sday = DAY * (start / DAY)
        eday = DAY * (end / DAY)

        days = list(range(sday, eday+1440, DAY))
        daystr = [time.strftime("%Y-%m-%d", time.gmtime(i)) for i in days]

        data = numpy.empty([hostcount, (end-start)/60], dtype='f4')
        # print "Data",data.shape

        pi = 0
        si = start/60
        # print "SI",si
        for day, str in zip(days, daystr):
            # print day
            daym = day/60
            dhostcount = self.getHostCount(day)
            ei = min(end/60, daym+DAYMIN)
            # print "EI",ei
            # print "EI-SI",(ei-si),si-daym
            if (ei-si):
                try:
                    daydata = self.ioctx.read(
                        str+"/"+key, length=(ei-si)*dhostcount*4, offset=(si-daym)*dhostcount*4)
                    # print "daydata",len(daydata),str
                    dayarray = numpy.frombuffer(daydata, dtype='f4')
                    dayarray.resize(ei-si, dhostcount)
                    dayarray = dayarray.transpose()
                except rados.ObjectNotFound:
                    # if the file is not there yet, which happens around the day start, return blank data
                    # print "no file"
                    dayarray = numpy.zeros((hostcount, ei-si), dtype='f4')
                except ValueError:
                    print("ValueError", daydata, ei, si)
                    dayarray = numpy.zeros((hostcount, ei-si), dtype='f4')
                # print dayarray.shape,daym
                # print si,ei,pi,ei-si,pi+ei-si,si-daym,ei-daym

                # print data[:dhostcount,pi:pi+ei-si].shape, dayarray.shape
                # print dayarray.shape[1], pi+ei-si
                # if dayarray[::].shape[1] == pi+ei-si:
                #	dayarray=dayarray[:,:-1]
                # [:,si-daym:ei-daym]
                data[:dhostcount, pi:pi+ei-si] = dayarray[::]

            pi += ei-si
            si = ei

        if hostlist:
            idx = [self.hostindex(o) for o in hostlist]
            # throw out any indexes that are bigger than hostcount
            idx = [i for i in idx if i < hostcount]
            # print data.shape,idx
            data = data.take(idx, 0)

        return data.take(list(range(data.shape[1]-1, -1, -1)), 1)

    def getYTicks(self, start, end):
        s = prevmin(start)/60
        e = prevmin(end)/60
        # print "S,E",s,e,e-s
        ticks = [time.strftime("%F %R", time.localtime(i*60))
                 for i in range(s, e)]
        ticks.reverse()
        return ticks

    def getHostCount(self, t):
        # print "getHostCount("+str(t)+")"
        if abs(self.hostcachetime-t) > 60*60:
            num = 0
            hosl = self.ioctx.read("hostorder.sizelog")
            hostsizes = hosl.split("\n")
            for line in hostsizes:
                if len(line) < 1 or line[0] == '#':
                    continue
                date, count = line.split()
                d = int(date)
                c = int(count)
                if d <= t:
                    num = c
            self.hostcount = num
            self.hostcachetime = t
        return self.hostcount


if __name__ == "__main__":

    #rds = RadosDataStore("/etc/ceph/ceph.conf","chinook")
    rds = RadosDataStore("/etc/ceph/ceph.conf", "pic")
    t = int(time.time())
    d = rds.getDataSlice(t-(128*60), t, "cputotals.user")
    d.tofile("/tmp/file")

    print(rds.getXTicks())
    print(rds.getYTicks(t-(128*60), t))
    print(rds.getHostCount(t))
    print(rds.getHostCount(1343718000))
    print(rds.getHostCount(1356940800))
