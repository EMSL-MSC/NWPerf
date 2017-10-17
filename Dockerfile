FROM ubuntu:xenial

MAINTAINER karcaw@gmail.com

RUN apt-get update
RUN apt-get install -y wget apt-transport-https
#from the ceph install page at http://docs.ceph.com/docs/master/start/quick-start-preflight/#advanced-package-tool-apt
RUN wget -q -O- 'https://download.ceph.com/keys/release.asc' | apt-key add -
RUN echo deb https://download.ceph.com/debian/ xenial main | tee /etc/apt/sources.list.d/ceph.list
#end ceph

RUN apt-get update
RUN apt-get install -y eatmydata python python-zmq python-ceph python-simplejson python-numpy python-pip
RUN pip install python-hostlist

ENV PATH /bin:/sbin:/usr/bin:/usr/sbin:/app/bin:/app/sbin/
ENV PYTHONPATH /app/lib

ADD . /app
ADD conf/nwperf.conf /etc/

