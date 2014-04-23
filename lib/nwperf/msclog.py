#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle "BSD-style" open source license;
# the full text of that license is available in the COPYING file in the root of the repository
#
# Author: Evan J. Felix

import logging.handlers
import time
import threading
from logging import *
from SocketServer import *
import pickle
import sys

def setLevel(lvl):
    log.setLevel(lvl)

def logToError():
    _shdlr = StreamHandler(sys.stderr)
    _shdlr.setFormatter(_formatter)
    log.addHandler(_shdlr)

def logToFile(filename):
    _fhdlr = FileHandler(filename)
    _fhdlr.setFormatter(_formatter)
    log.addHandler(_fhdlr)
    
def logToUDP():
    _uhdlr = logging.handlers.DatagramHandler("localhost",logging.handlers.DEFAULT_UDP_LOGGING_PORT)
    log.addHandler(_uhdlr)
    setLevel(DEBUG)

def logToSyslog():
    _shdlr = logging.handlers.SysLogHandler("/dev/log")
    _shdlr.setFormatter(_formatter);
    log.addHandler(_shdlr)


# Setup default logging for root
log = getLogger("root")
_formatter = Formatter('%(asctime)s %(name)s:%(process)d:%(levelname)s %(filename)s:%(lineno)d %(message)s')
#logToError()
setLevel(WARNING)
logToUDP()
#logToSyslog()

#classed for the GUI portion
class UDPLogHandler(DatagramRequestHandler):
    def handle(s):
        print "handle:"
        
        data=pickle.loads(s.packet[4:])
        print data
        record=makeLogRecord(data)
        print record
        
        
    def finish(s):
        pass

class UDPLogServer(ThreadingUDPServer,threading.Thread):
    def __init__(s,address=("localhost",logging.handlers.DEFAULT_UDP_LOGGING_PORT),handler=None):
        if not handler:
            handler=UDPLogHandler
        ThreadingUDPServer.__init__(s,address,handler)
        threading.Thread.__init__(s,name="UDPServer")
        s.setDaemon(True)
        s.start()
        

    def run(s):
        s.serve_forever()
    
class UDPLogShortHandler(DatagramRequestHandler):
    def handle(s):
        
        data=pickle.loads(s.packet[4:])
        text=data['msg']%(data['args'])
        #print data
        #print "%(threadName)s:%(name)s:%(filename)s:%(lineno)s:"%(data)+text
        record=makeLogRecord(data)
        print _formatter.format(record)
        
        
    def finish(s):
        pass

def handle_term():
	global _running
	running=0
