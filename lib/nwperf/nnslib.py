#!/bin/env python26
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
				self.nssock.send_multipart(("1", "addService", service, location, str(timeout), socketType, dataType))
			else:
				self.nssock.send_multipart(("1", "addService", service, location, str(timeout), socketType))
		else:
			self.nssock.send_multipart(("1", "addService", service, location, str(timeout)))
		ret = self.nssock.recv_multipart()
		if ret[0] == "ERROR":
			raise NameServerException(ret[1])

	def publishService(self, service, location, timeout, socketType=None, dataType=None):
		timeout = int(timeout)
		try:
			self.services[service][location] = (timeout, time.time()+timeout/2)
		except KeyError:
			self.services[service] = {location:(timeout, time.time()+timeout/2)}
		self.addService(service, location, timeout, socketType, dataType)

	def updateServices(self):
		for (service, value) in self.services.iteritems():
			for (location, timeouts) in value.iteritems():
				if time.time() > timeouts[1]:
					self.addService(service, location, timeouts[0])
					self.services[service][location] = (timeouts[0], time.time()+timeouts[0]/2)
		
	def removeServices(self):
		for (service, value) in self.services.iteritems():
			self.nssock.send_multipart(("1", "removeService", service, value.keys()[0]))
		
	def removeService(self, service, locations = None):
		if locations == None:
			self.nssock.send_multipart(("1", "removeService", service))
		else:
			self.nssock.send_multipart(("1", "removeService", service, location))
		ret = self.nssock.recv_multipart()
		if ret[0] == "ERROR":
			raise NameServerException(ret[1])
		try:
			del self.services[service][location]
		except:
			pass
		if service in self.services and len(self.services[service]) == 0:
			del self.services[service]

	def replaceService(self, service, location, timeout):
		timeout = int(timeout)
		try:
			del(self.services[service])
		except:
			pass
		self.services[service] = {location:(timeout, time.time()+timeout/2)}
		self.nssock.send_multipart(("1", "replaceService", service, location, str(timeout)))
		ret = self.nssock.recv_multipart()
		if ret[0] == "ERROR":
			raise NameServerException(ret[1])

	def describeService(self, service):
		self.nssock.send_multipart(("1", "describeService", service))
		ret = self.nssock.recv_multipart()
		if ret[0] == "ERROR":
			raise NameServerException(ret[1])
		else:
			return ret

	def getService(self, service):
		self.nssock.send_multipart(("1", "getService", service))
		ret = self.nssock.recv_multipart()
		if ret[0] == "ERROR":
			raise NameServerException(ret[1])
		else:
			return zip(ret[::2],[int(i) for i in ret[1::2]])

	def listServices(self):
		self.nssock.send_multipart(("1", "listServices"))
		ret = self.nssock.recv_multipart()
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
			self.sockets.setdefault(socket,{}).setdefault(service,{location:None})[location] = expires

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
		self.nssock.send_multipart(("1", "addDataType", dataType, dataFormat, requiredFields, optionalFields))
		ret = self.nssock.recv_multipart()
		if ret[0] == "ERROR":
			raise NameServerException(ret[1])

        def listDataTypes(self):
		self.nssock.send_multipart(("1", "listDataTypes"))
		ret = self.nssock.recv_multipart()
		if ret[0] == "ERROR":
			raise NameServerException(ret[1])
		else:
			return ret

        def getDataType(self, dataType):
		self.nssock.send_multipart(("1", "getDataType", dataType))
		ret = self.nssock.recv_multipart()
		if ret[0] == "ERROR":
			raise NameServerException(ret[1])
		else:
			return ret

        def removeDataType(self, dataType):
		self.nssock.send_multipart(("1", "removeDataType", dataType))
		ret = self.nssock.recv_multipart()
		if ret[0] == "ERROR":
			raise NameServerException(ret[1])
