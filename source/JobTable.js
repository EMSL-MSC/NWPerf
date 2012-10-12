enyo.kind({
        name: "JobTable",
	kind: "FittableRows",
	published: {
		jobs: [],
		showUsers: false,
	},
	events: {
		onJobSelected: "",
	},
        components:[
		{kind: "FittableColumns", components: [
			{style: "width: 9%; font-weight: bold;", content: "Job ID"},
			{style: "width: 9%; font-weight: bold;", content: "Account"},
			{style: "width: 9%; font-weight: bold;", showing: false, content: "User", name: "userHeader"},
			{style: "width: 17%; font-weight: bold;", content: "Submit Time"},
			{style: "width: 17%; font-weight: bold;", content: "Start Time"},
			{style: "width: 17%; font-weight: bold;", content: "End Time"},
			{style: "width: 10%; font-weight: bold;", content: "Run Time"},
			{style: "width: 12%; font-weight: bold;", content: "Number of Nodes"},
		]},
		{kind: "List", fit: true, name: "jobList", onSetupItem: "addJob", toggleSelected: true, components: [
			{kind: "FittableColumns", ontap: "jobTap", components: [
				{style: "width: 9%;", name: "jobId"},
				{style: "width: 9%;", name: "account"},
				{style: "width: 9%;", name: "user", showing: false},
				{style: "width: 17%;", name: "submitTime"},
				{style: "width: 17%;", name: "startTime"},
				{style: "width: 17%;", name: "endTime"},
				{style: "width: 10%; text-align: right;", name: "runTime"},
				{style: "width: 12%; text-align: right;", name: "nodes"},
			]},
		]}
        ],

	jobsChanged: function(oldValue) {
		this.$.jobList.setCount(this.jobs.length);
		this.$.jobList.refresh();
	},
	showUsersChanged: function(oldValue) {
		this.$.userHeader.setShowing(this.showUsers);
		this.$.jobList.refresh();
	},
	addJob: function(inSender, inEvent) {
		job = this.jobs[inEvent.index];
		this.$.user.setContent(job.user);
		this.$.user.setShowing(this.showUsers);
		this.$.jobId.setContent(job.id);
		this.$.account.setContent(job.account);
		this.$.nodes.setContent(job.numnodes);
		this.$.submitTime.setContent(job.submittime);
		this.$.startTime.setContent(job.starttime);
		this.$.endTime.setContent(job.endtime);
		this.$.runTime.setContent(job.runtime);
	},

	jobTap: function(inSender, inEvent) {
		this.doJobSelected(this.jobs[inEvent.index]);
	}
});
