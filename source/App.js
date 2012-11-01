enyo.kind({
	name: "App",
	kind: "FittableRows",
	components:[
		{kind: "UserManager", name: "userManager", onGroupMembership: "updateUserGroup", onUserListRetrieved:"updateUserList"},
		{kind: "JobManager", name: "jobManager", onNewJobList: "updateJobTable", onNewJob:"displayJob"},
		{kind: "QueryBuilder", name: "queryBuilder", onQueryChanged: "getJobList"},
		{kind: "Panels", draggable: false, name: "jobViews", fit: true, arrangerKind: "CollapsingArranger", realtimeFit: true, components: [
			{kind: "JobTable", name: "jobTable", onJobSelected: "getJob", style: "width: 100%;"},
			{kind: "JobView", name: "jobView", style: "width: 0%;", onJobViewClosed: "closeJobView"},
		]},
	],
	ready: false,
	create: function() {
		this.inherited(arguments);
		this.$.userManager.getGroupMembership();
		this.ready = true;
	},
	updateUserGroup: function(inSender, inEvent) {
		for(i = 0; i < inEvent.length; i++) {
			if(inEvent[i] == "admin") {
				//this.$.userManager.getUserList();
				this.$.queryBuilder.setAllowUserSelect(true);
				this.$.jobTable.setShowUsers(true);
				break;
			}
		}
	},
	updateUserList: function(inSender, inEvent) {
		this.$.queryBuilder.setUserList(inEvent);
	},
	getJobList: function(inSender, inEvent) {
		this.$.jobManager.getJobList(inEvent);
		if(this.ready) {
			this.$.jobTable.spin();
			this.$.jobViews.setIndex(0);
		}
	},
	updateJobTable: function(inSender, inEvent) {
		this.$.jobTable.setJobs(inEvent);
	},
	getJob: function(inSender, inEvent) {
		this.$.jobManager.getJob(inEvent.jobid);
		this.$.jobView.spin();
	},
	displayJob: function(inSender, inEvent) {
		this.$.jobView.setJob(inEvent);
		this.$.jobViews.setIndex(1);
	},
	closeJobView: function(inSender, inEvent) {
		this.$.jobViews.setIndex(0);
	},
});
