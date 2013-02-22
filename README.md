NWPerf
======

Cluster performance data collection tools


Dependencies
============

The NWPerf collection scripts depend heavily on the [ZeroMQ](http://www.zeromq.org/) Python modules. You can this library on various Linux Platforms:

  * Ubuntu/debian
    `apt-get install python-zmq`
  * Redhat
    `yum install python-zmq`



Ceph Point Storage
==================

In order to use the ceph point storage tools (gen_cview,nwperf-ceph-store.py) you will need a configured [Ceph](www.ceph.com) rados system.  You then create a rados pool for the cluster of points you want to store.  You then need to populate the pool with these files:

	* hostorder - a ordered list of hostnames that will be stored in points tables
	* hostorder.sizelog - A history of size changes, initially contains only the host count
	* pointdesc - descriptions of the metrics stored in the database.
	* pointindex - a list of all metrics stored in the pool

Pool Creation Steps
-------------------

	1. Create rados pool
	1. Populate basic files
	1. Collect Data
  1. Output

