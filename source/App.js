enyo.kind({
	name: "App",
	fit: true,
	kind: "Panels",
	components:[
		{kind: "JobManager", name: "jobManager", onNewJobList: "updateJobTable"},
		{kind: "QueryBuilder", style: "height: 30%", onQueryChanged: "getJobList"},
		{kind: "Panels", components: [
			//{kind: "JobTable"},
			//{kind: "JobView"},
		]},
	],
	getJobList: function(inSender, inEvent) {
		console.log("getJobList", arguments);
		this.$.jobManager.getJobList(inEvent);
	},
	updateJobTable: function(inSender, inEvent) {
		console.log("updateJobTable", inSender, inEvent);
	},
});
