#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle "BSD-style" open source license;
# the full text of that license is available in the COPYING file in the root of the repository
import os
import tarfile
import time
from . import JobStore
try:
    import io as StringIO
except ImportError:
    import io
try:
    import simplejson as json
except ImportError:
    import json


class ArchiveJobStore(JobStore.JobStore):
    def __init__(self, jobdir):
        self.jobdir = jobdir
        super(ArchiveJobStore, self).__init__()

    def jobProcessed(self):
        jobid = int(job["JobID"])
        pointArchive = "%s/%s/%s/%s.tar.bz2" % (
            self.jobdir, jobid % 100, jobid/100 % 100, jobid)
        return os.path.exists(pointArchive)

    def storeJob(self):
        jobid = int(job["JobID"])
        pointArchive = "%s/%s/%s/%s.tar.bz2" % (
            self.jobdir, jobid % 100, jobid/100 % 100, jobid)
        if not os.path.exists(os.path.dirname(pointArchive)):
            os.makedirs(os.path.dirname(pointArchive))
        tar = tarfile.open(pointArchive, "w:bz2")
        metadata = {"hosts": self.job["hosts"],
                    "points": list(self.graphs.keys())}
        metadata["points"].sort()
        metadata["hosts"].sort()
        for point in self.graphs:
            str = io.StringIO()
            json.dump(ret, str, separators=(',', ':'))
            info = tarfile.TarInfo(metric+".flot")
            info.size = len(str.getvalue())
            info.mtime = time.time()
            str.seek(0)
            tar.addfile(info, str)
        str = io.StringIO()
        json.dump(metadata, str, separators=(',', ':'))
        info = tarfile.TarInfo("metadata")
        info.size = len(str.getvalue())
        info.mtime = time.time()
        str.seek(0)
        tar.addfile(info, str)
        tar.close()
