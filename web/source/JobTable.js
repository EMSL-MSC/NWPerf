/*
 * Copyright 2013 Battelle Memorial Institute.
 * This software is licensed under the Battelle “BSD-style” open source license;
 * the full text of that license is available in the COPYING file in the root of the repository
 */
enyo.kind({
        name: "JobTable",
	kind: "FittableRows",
	classes: "enyo-selectable JobTable",
	published: {
		jobs: [],
		showUsers: false
	},
	events: {
		onJobSelected: ""
	},
        components:[
		{name: "spinnerPopup", kind: "onyx.Popup", centered: true, floating: true, components: [
			{kind: "onyx.Spinner"}
		]},
		{kind: "FittableColumns", classes: "JobTable-header-container", components: [
			{classes: "JobTable-header", style: "width: 9%", ontap: "sortColumn", content: "Job ID", name: "JobIDHeader"},
			{classes: "JobTable-header", style: "width: 9%", ontap: "sortColumn", content: "Account", name: "AccountHeader"},
			{classes: "JobTable-header", style: "width: 9%", ontap: "sortColumn", showing: false, content: "User", name: "UserHeader"},
			{classes: "JobTable-header", style: "width: 16%", ontap: "sortColumn", content: "Submit Time", name: "SubmitHeader"},
			{classes: "JobTable-header", style: "width: 16%", ontap: "sortColumn", content: "Start Time", name: "StartHeader"},
			{classes: "JobTable-header", style: "width: 16%", ontap: "sortColumn", content: "End Time", name: "EndHeader"},
			{classes: "JobTable-header", style: "width: 11%", ontap: "sortColumn", content: "Run Time", name: "RunTimeHeader"},
			{classes: "JobTable-header", style: "width: 14%", ontap: "sortColumn", content: "Node Count", name: "NumNodesHeader"}
		]},
		{kind: "List", fit: true, name: "jobList", onSetupItem: "addJob", toggleSelected: true, components: [
			{kind: "FittableColumns", classes: "JobTable-row", ontap: "jobTap", components: [
				{classes: "JobTable-cell", style: "width: 9%;", name: "jobId"},
				{classes: "JobTable-cell", style: "width: 9%;", name: "account"},
				{classes: "JobTable-cell", style: "width: 9%;", name: "user", showing: false},
				{classes: "JobTable-cell", style: "width: 16%;", name: "submitTime"},
				{classes: "JobTable-cell", style: "width: 16%;", name: "startTime"},
				{classes: "JobTable-cell", style: "width: 16%;", name: "endTime"},
				{classes: "JobTable-cell", style: "width: 11%; text-align: right;", name: "runTime"},
				{classes: "JobTable-cell", style: "width: 14%; text-align: right;", name: "nodes"}
			]}
		]}
        ],
	spin: function() {
		this.$.spinnerPopup.show();
	},
	curSortedColumn: null,
	curSortedOrder: null,
	sortColumn: function(inSender, inEvent) {
		if(this.curSortedColumn == inSender) {
			if(this.curSortedOrder == "desc") {
				this.curSortedColumn.setClasses("JobTable-header-asc");
				this.curSortedOrder = "asc";
			} else {
				this.curSortedColumn.setClasses("JobTable-header-desc");
				this.curSortedOrder = "desc";
			}
		} else {
			if(this.curSortedColumn) {
				this.curSortedColumn.setClasses("JobTable-header");
			}
			this.curSortedColumn = inSender;
			this.curSortedOrder = "asc";
			this.curSortedColumn.setClasses("JobTable-header-asc");
		}
		var field = inSender.name.replace("Header", "");
		if(field == "NumNodes" || field == "JobID" || field == "RunTime") {
			if(this.curSortedOrder == "asc") {
				var sortFunc = function(a,b) { return parseInt(a[field]) - parseInt(b[field]); }
			} else {
				var sortFunc = function(a,b) { return parseInt(b[field]) - parseInt(a[field]); }
			}
		} else {
			if(this.curSortedOrder == "asc") {
				var sortFunc = function(a,b) {
					if(a[field] == null)
						a[field] = "";
					if(b[field] == null) 
						b[field] = "";
						
					return a[field].localeCompare(b[field]);
				}
			} else {
				var sortFunc = function(a,b) {
					if(a[field] == null)
						a[field] = "";
					if(b[field] == null) 
						b[field] = "";
						
					return b[field].localeCompare(a[field]);
				}
			}
		}
		this.jobs.sort(sortFunc);
		this.$.spinnerPopup.hide();
		this.$.jobList.setCount(this.jobs.length);
		this.$.jobList.refresh();
	},
	jobsChanged: function(oldValue) {
		if(this.curSortedColumn != null) 
			this.curSortedColumn.setClasses("JobTable-header");
		this.curSortedColumn = null;
		this.curSortedOrdered = null;
		this.sortColumn(this.$.JobIDHeader);
	},
	showUsersChanged: function(oldValue) {
		this.$.UserHeader.setShowing(this.showUsers);
		this.$.jobList.refresh();
	},
	addJob: function(inSender, inEvent) {
		var job = this.jobs[inEvent.index];
		this.$.user.setContent(job.User);
		this.$.user.setShowing(this.showUsers);
		this.$.jobId.setContent(job.JobID);
		this.$.account.setContent(job.Account);
		this.$.nodes.setContent(job.NumNodes);
		this.$.submitTime.setContent(job.Submit);
		this.$.startTime.setContent(job.Start);
		this.$.endTime.setContent(job.End);
		this.$.runTime.setContent(job.RunTime);
	},

	jobTap: function(inSender, inEvent) {
		this.doJobSelected(this.jobs[inEvent.index]);
	}
});
