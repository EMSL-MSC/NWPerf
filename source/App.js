enyo.kind({
	name: "App",
	components:[
		{kind: "AdminInterface", name: "adminInterface", centered: true, modal: true, scrim: true},
		{kind: "UserManager", name: "userManager", onGroupMembership: "updateUserGroup", onUserListRetrieved:"updateUserList"},
		{kind: "JobManager", name: "jobManager", onNewJobList: "updateJobTable", onNewJob:"displayJob"},
		{kind: "Panels", name: "mainPanel", style: "height: 100%", draggable: false, arrangerKind: "CollapsingArranger", components: [
			{kind: "FittableRows", name: "jobViews", realtimeFit: true, style: "width: 100%;", components: [
				{kind: "FittableColumns", classes: "header", components: [
					{classes: "logo", components: [
						{kind: "Image", src: "assets/logo.png"},
					]},
					{kind: "QueryBuilder", name: "queryBuilder", onQueryChanged: "getJobList"},
				]},
				{kind: "JobTable", name: "jobTable", fit: true, onJobSelected: "getJob"},
				{kind: "onyx.Toolbar", components: [
					{kind: "onyx.Button", name: "adminButton", content: "Admin", showing: false, ontap: "showAdmin"},
				]}
			]},
			{kind: "JobView", name: "jobView", style: "width: 0%;", onJobViewClosed: "closeJobView"}
		]}
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
				this.$.adminButton.setShowing(true);
				this.$.adminInterface.updateValues();
				this.render();
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
			this.$.mainPanel.setIndex(0);
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
		this.$.mainPanel.setIndex(1);
	},
	closeJobView: function(inSender, inEvent) {
		this.$.mainPanel.setIndex(0);
	},
	showAdmin: function(inSender, inEvent) {
		this.$.adminInterface.show();
	}
});
