NWPerf
======

Cluster performance data collection tools


Dependencies
============

The NWPerf collection scripts depend heavily on the [ZeroMQ](http://www.zeromq.org/) Python modules. You can this library on various Linux Platforms:

* Ubuntu/debian:

    `apt-get install python-zmq`

* Redhat:

    `yum install python-zmq`



Ceph Point Storage
==================

In order to use the ceph point storage tools (gen_cview,nwperf-ceph-store.py) you will need a configured [Ceph](www.ceph.com) rados system.  You then create a rados pool for the cluster of points you want to store.  You then need to populate the pool with these files:

  * hostorder - a ordered list of hostnames that will be stored in points tables
  * hostorder.sizelog - A history of size changes, initially contains only the host count
  * pointdesc - descriptions of the metrics stored in the database. a basic one covering many collectl and ganglia data point is included in the examples directory
  * pointindex - a list of all metrics stored in the pool

Pool Creation Steps
-------------------
We will create a pool for a cluster called io, with 38 nodes names io1 to io38. It is assumed that you already have some sort of collection system setup. In this case we are using the nwperf-ganglia.py script, and will gather points from it. Since it published all the point information to the NWPerf Nameserver we can get a list of point from the nameserver.

  1. Create rados pool

    ```
    rados mkpool io.points
    ceph osd pool set io.points size 3
    ```
    It is not required to set the redundancy level to 3, the default is 2
  1. Populate basic files
    ```
seq -f io%g 1 38 > /tmp/hostorder
echo 0 38 > /tmp/hostorder.sizelog
nwperf-nsq.py tcp://nwperf-ns:6967 listServices | grep io | sed -e 's/^io.//' -e '/multipart/d' | sort > /tmp/pointindex
rados -p io.points put hostorder /tmp/hostorder
rados -p io.points put hostorder.sizelog /tmp/hostorder.sizelog
rados -p io.points put pointdesc ~/NWPerf/examples/pointdesc
rados -p io.points put pointindex /tmp/pointindex
rados -p io.points ls
```
    The final command allows you to verify that all files are present in the rados pool.

  1. Collect Data
  1. Output

