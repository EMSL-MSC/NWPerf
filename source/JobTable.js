enyo.kind({
        name: "JobTable",
	kind: "FittableRows",
	published: {
		jobs: [],
	},
	events: {
		onJobSelected: "",
	},
        components:[
		{kind: "FittableColumns", components: [
			{style: "width: 10%; font-weight: bold;", content: "Job ID"},
			{style: "width: 10%; font-weight: bold;", content: "Account"},
			{style: "width: 18%; font-weight: bold;", content: "Submit Time"},
			{style: "width: 18%; font-weight: bold;", content: "Start Time"},
			{style: "width: 18%; font-weight: bold;", content: "End Time"},
			{style: "width: 12%; font-weight: bold;", content: "Run Time"},
			{style: "width: 14%; font-weight: bold;", content: "Number of Nodes"},
		]},
		{kind: "List", fit: true, name: "jobList", onSetupItem: "addJob", components: [
			{kind: "FittableColumns", ontap: "jobTap", components: [
				{style: "width: 10%;", name: "jobId"},
				{style: "width: 10%;", name: "account"},
				{style: "width: 18%;", name: "submitTime"},
				{style: "width: 18%;", name: "startTime"},
				{style: "width: 18%;", name: "endTime"},
				{style: "width: 12%; text-align: right;", name: "runTime"},
				{style: "width: 14%; text-align: right;", name: "nodes"},
			]},
		]}
        ],

	jobsChanged: function(oldValue) {
		this.$.jobList.setCount(this.jobs.length);
		this.$.jobList.refresh();
	},

	addJob: function(inSender, inEvent) {
		job = this.jobs[inEvent.index];
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
