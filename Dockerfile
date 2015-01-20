FROM ubuntu:trusty

MAINTAINER karcaw@gmail.com

RUN apt-get update
RUN apt-get install -y eatmydata python python-zmq python-ceph python-simplejson python-numpy

ENV PATH /bin:/sbin:/usr/bin:/usr/sbin:/app/bin:/app/sbin/
ENV PYTHONPATH /app/lib

ADD . /app
ADD conf/nwperf.conf /etc/

