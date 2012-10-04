enyo.kind({
        name: "JobTable",
        fit: true,
	tag: "table",
	published: {
		jobs: [],
	},
	events: {
		onJobSelected: "",
	},
        components:[
		{tag: "tr", components: [
			{tag: "th", content: "Job ID"},
			{tag: "th", content: "Account"},
			{tag: "th", content: "Nodes"},
			{tag: "th", content: "Submit Time"},
			{tag: "th", content: "Start Time"},
			{tag: "th", content: "End Time"},
			{tag: "th", content: "Run Time"},
		]},
		{kind: "List", name: "jobList", onSetupItem: "addJob", components: [
			{tag: "tr", ontap: "jobTap", components: [
				{tag: "td", name: "jobId"},
				{tag: "td", name: "account"},
				{tag: "td", name: "nodes"},
				{tag: "td", name: "submitTime"},
				{tag: "td", name: "startTime"},
				{tag: "td", name: "endTime"},
				{tag: "td", name: "runTime"}
			]},
		]},
        ],

	jobsChanged: function(oldValue) {
		this.$.jobList.setCount(this.jobs.length);
	},

	addJob: function(inSender, inEvent) {
		job = this.jobs[inEvent.index];
		this.$.jobId.setContent(job["jobId"])
		this.$.account.setContent(job["account"])
		this.$.nodes.setContent(job["nodes"])
		this.$.submitTime.setContent(job["submitTime"])
		this.$.startTime.setContent(job["startTime"])
		this.$.endTime.setContent(job["endTime"])
		this.$.runTime.setContent(job["runTime"])
	},

	jobTap: function(inSender, inEvent) {
		inSender.setClass("SelectedJob");
		this.doJobSelected(this.jobs[inEvent.index]);
	}
});
