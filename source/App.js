enyo.kind({
	name: "App",
	kind: "FittableRows",
	components:[
		{kind: "JobManager", name: "jobManager", onNewJobList: "updateJobTable", onNewJob:"displayJob"},
		{kind: "QueryBuilder", classes: "shadow", style: "height: 20%", onQueryChanged: "getJobList"},
		{kind: "Panels", draggable: false, name: "jobViews", fit: true, arrangerKind: "CollapsingArranger", realtimeFit: true, components: [
			{kind: "JobTable", name: "jobTable", onJobSelected: "getJob", style: "width: 100%;"},
			{kind: "JobView", name: "jobView", style: "width: 0%;", onJobViewClosed: "closeJobView"},
		]},
	],
	getJobList: function(inSender, inEvent) {
		console.log("getJobList", arguments);
		this.$.jobManager.getJobList(inEvent);
		this.$.jobViews.setIndex(0);
	},
	updateJobTable: function(inSender, inEvent) {
		console.log("updateJobTable", inSender, inEvent);
		this.$.jobTable.setJobs(inEvent);
	},
	getJob: function(inSender, inEvent) {
		console.log("getJob", inSender, inEvent);
		this.$.jobManager.getJob(inEvent.jobid);
		this.$.jobView.spin();
		this.$.jobViews.setIndex(1);
	},
	displayJob: function(inSender, inEvent) {
		console.log("displayJob", inSender, inEvent);
		this.$.jobView.setJob(inEvent);
	},
	closeJobView: function(inSender, inEvent) {
		this.$.jobViews.setIndex(0);
	},
});
