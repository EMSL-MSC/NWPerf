enyo.kind({
        name: "MetricManager",
	kind: "Component",
	events: {
		onNewMetricList: "",
		onNewMetric: ""
	},
	metricListTag: 0,
	getMetricList: function() {
		metricListReq = new enyo.Ajax({url: "Metrics/"})
		.response(this, function(inSender, inResponse) {
			if(parseInt(inResponse.tag) == this.metricListTag) {
				this.doNewMetricList(inResponse.metrics);
			}
		})
		.go({tag: ++this.metricListTag});
		return metricListReq;
	},
	getMetricTag: 0,
	getMetric: function(metricName) {
		return new enyo.Ajax({url: "Metrics/"+metricName})
		.response(this, function(inSender, inResponse) {
			if(parseInt(inResponse.tag) == this.getMetricTag) {
				delete inResponse.tag
				this.doNewMetric(inResponse);
			}
		})
		.go({tag: ++this.getMetricTag});
		
	},
	updateMetric: function(name, metric) {
		return new enyo.Ajax({url: "Metrics/"+name, method: "PUT"}).go(metric);
	},
	deleteMetric: function(name) {
		return new enyo.Ajax({url: "Metrics/"+name, method: "DELETE"}).go();
	}
});
