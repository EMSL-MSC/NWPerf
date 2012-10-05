enyo.kind({
        name: "JobManager",
	kind: "Component",
	events: {
		onNewJobList: "",
		onNewJob: "",
	},
	jobListReq: false,
	getJobList: function(query) {
		this.jobListReq = new enyo.Ajax({url: "job/"});
		this.jobListReq.response(function(inSender, inResponse) {
			this.doNewJobList(inResponse);
		});
		this.jobListReq.go({q: query});
	},
	jobReq: false,
	getJob: function(jobId) {
		this.jobReq = new enyo.Ajax({url: "job/"+jobId});
		this.jobReq.response(function(inSender, inResponse) {
			this.doNewJob(inResponse);
		});
		this.jobReq.go();
	},
});
