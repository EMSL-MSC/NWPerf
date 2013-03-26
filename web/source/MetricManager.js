/*
 * Copyright 2013 Battelle Memorial Institute.
 * This software is licensed under the Battelle “BSD-style” open source license;
 * the full text of that license is available in the COPYING file in the root of the repository
 */
enyo.kind({
        name: "MetricManager",
	kind: "Component",
	url: "metrics/",
	events: {
		onNewMetricList: "",
		onNewMetric: ""
	},
	metricListTag: 0,
	getMetricList: function() {
		return new enyo.Ajax({url: this.url})
		.response(this, function(inSender, inResponse) {
			if(parseInt(inResponse.tag) == this.metricListTag) {
				this.doNewMetricList(inResponse.metrics);
			}
		})
		.go({tag: ++this.metricListTag});
	},
	getMetricTag: 0,
	getMetric: function(metricName) {
		return new enyo.Ajax({url: this.url+metricName})
		.response(this, function(inSender, inResponse) {
			if(parseInt(inResponse.tag) == this.getMetricTag) {
				delete inResponse.tag
				this.doNewMetric(inResponse);
			}
		})
		.go({tag: ++this.getMetricTag});
		
	},
	updateMetric: function(name, metric) {
		return new enyo.Ajax({url: this.url+name, method: "PUT"}).go(metric);
	},
	deleteMetric: function(name) {
		return new enyo.Ajax({url: this.url+name, method: "DELETE"}).go();
	}
});
