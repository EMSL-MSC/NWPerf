#!/bin/env python26
# -*- coding: latin-1 -*-
#
# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle "BSD-style" open source license;
# the full text of that license is available in the COPYING file in the root of the repository
import zmq
import time
import os
import sys


class NameServerException(Exception):
    pass


class ServiceExpiredException(Exception):
    def __init__(self, service, socket):
        self.service = service
        self.socket = socket

    def __str__(self):
        return "Service %s expired on socket %s" % (service, socket)


class NameServer(object):
    def __init__(self, nameServer):
        if ":" not in nameServer:
            nameServer = "tcp://%s:6967" % nameServer
        ctx = zmq.Context()
        self.nssock = ctx.socket(zmq.REQ)
        self.nssock.connect(nameServer)
        self.services = {}
        self.sockets = {}

    def addService(self, service, location, timeout, socketType=None, dataType=None):
        timeout = int(timeout)
        if socketType != None:
            if dataType != None:
                self.nssock.send_multipart(
                    (b"1", b"addService", service.encode(), location.encode(), str(timeout).encode(), socketType.encode(), dataType.encode()))
            else:
                self.nssock.send_multipart(
                    (b"1", b"addService", service.encode(), location.encode(), str(timeout).encode(), socketType.encode()))
        else:
            self.nssock.send_multipart(
                (b"1", b"addService", service.encode(), location.encode(), str(timeout).encode()))
        ret = self.nssock.recv_multipart()
        ret = [i.decode() for i in ret]
        if ret[0] == "ERROR":
            raise NameServerException(ret[1])
        return ret

    def publishService(self, service, location, timeout, socketType=None, dataType=None):
        timeout = int(timeout)
        try:
            self.services[service][location] = (timeout, time.time()+timeout/2)
        except KeyError:
            self.services[service] = {
                location: (timeout, time.time()+timeout/2)}
        self.addService(service, location, timeout, socketType, dataType)

    def updateServices(self):
        for (service, value) in self.services.items():
            for (location, timeouts) in value.items():
                if time.time() > timeouts[1]:
                    self.addService(service, location, timeouts[0])
                    self.services[service][location] = (
                        timeouts[0], time.time()+timeouts[0]/2)

    def removeServices(self):
        for (service, value) in self.services.items():
            self.nssock.send_multipart(
                (b"1", b"removeService", service, list(value.keys())[0]))

    def removeService(self, service, locations=None):
        if locations == None:
            self.nssock.send_multipart((b"1", b"removeService", service.encode()))
        else:
            self.nssock.send_multipart(
                (b"1", b"removeService", service, locations.encode()))
        ret = self.nssock.recv_multipart()
        ret = [i.decode() for i in ret]
        if ret[0] == "ERROR":
            raise NameServerException(ret[1])
        try:
            del self.services[service][locations]
        except:
            pass
        if service in self.services and len(self.services[service]) == 0:
            del self.services[service]
        return ret
    def replaceService(self, service, location, timeout):
        timeout = int(timeout)
        try:
            del(self.services[service])
        except:
            pass
        self.services[service] = {location: (timeout, time.time()+timeout/2)}
        self.nssock.send_multipart(
            (b"1", b"replaceService", service.encode(), location.encode(), str(timeout).encode()))
        ret = self.nssock.recv_multipart()
        ret = [i.decode() for i in ret]
        if ret[0] == "ERROR":
            raise NameServerException(ret[1])
        return ret

    def describeService(self, service):
        self.nssock.send_multipart((b"1", b"describeService", service.encode()))
        ret = self.nssock.recv_multipart()
        ret = [i.decode() for i in ret]
        if ret[0] == "ERROR":
            raise NameServerException(ret[1])
        else:
            return ret

    def getService(self, service):
        self.nssock.send_multipart((b"1", b"getService", service.encode()))
        ret = self.nssock.recv_multipart()
        ret = [i.decode() for i in ret]
        if ret[0] == "ERROR":
            raise NameServerException(ret[1])
        else:
            return list(zip(ret[::2], [int(i) for i in ret[1::2]]))

    def listServices(self):
        self.nssock.send_multipart((b"1", b"listServices"))
        ret = self.nssock.recv_multipart()
        ret = [i.decode() for i in ret]
        if ret[0] == "ERROR":
            raise NameServerException(ret[1])
        else:
            return ret

    def connectService(self, socket, service):
        for (location, timeout) in self.getService(service):
            try:
                if location not in self.sockets[socket][service]:
                    socket.connect(location)
            except KeyError:
                socket.connect(location)
            expires = time.time() + timeout
            self.sockets.setdefault(socket, {}).setdefault(
                service, {location: None})[location] = expires

    def updateSocket(self, socket):
        for service in self.sockets[socket]:
            for location in self.sockets[socket][service]:
                now = time.time()
                if now > self.sockets[socket][service][location]:
                    self.connectService(socket, service)
                    if now > self.sockets[socket][service][location]:
                        del self.sockets[socket]
                        raise ServiceExpiredException(service, socket)

    def addDataType(self, dataType, dataFormat, requiredFields, optionalFields):
        self.nssock.send_multipart(
            (b"1", b"addDataType", dataType.encode(), dataFormat.encode(), requiredFields.encode(), optionalFields.encode()))
        ret = self.nssock.recv_multipart()
        ret = [i.decode() for i in ret]
        if ret[0] == "ERROR":
            raise NameServerException(ret[1])
        return ret

    def listDataTypes(self):
        self.nssock.send_multipart((b"1", b"listDataTypes"))
        ret = self.nssock.recv_multipart()
        ret = [i.decode() for i in ret]
        if ret[0] == "ERROR":
            raise NameServerException(ret[1])
        else:
            return ret

    def getDataType(self, dataType):
        self.nssock.send_multipart((b"1",b"getDataType", dataType.encode()))
        ret = self.nssock.recv_multipart()
        ret = [i.decode() for i in ret]
        if ret[0] == "ERROR":
            raise NameServerException(ret[1])
        else:
            return ret

    def removeDataType(self, dataType):
        self.nssock.send_multipart((b"1", b"removeDataType", dataType.encode()))
        ret = self.nssock.recv_multipart()
        ret = [i.decode() for i in ret]
        if ret[0] == "ERROR":
            raise NameServerException(ret[1])
        return ret
