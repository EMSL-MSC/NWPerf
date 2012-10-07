enyo.kind({
        name: "JobManager",
	kind: "Component",
	events: {
		onNewJobList: "",
		onNewJob: "",
	},
	jobListReq: false,
	getJobList: function(query) {
		this.jobListReq = new enyo.Ajax({url: "jobs/"})
		.response(this, function(inSender, inResponse) {
			this.doNewJobList(inResponse);
		})
		.go({q: JSON.stringify(query)});
		return this.jobListReq;
	},
	jobReq: false,
	getJob: function(jobId) {
		this.jobReq = new enyo.Ajax({url: "jobs/"+jobId})
		.response(this, function(inSender, inResponse) {
			this.doNewJob(inResponse);
		})
		.go();
		return this.jobReq;
	},
});
