enyo.kind({
	name: "App",
	fit: true,
	kind: "Panels",
	components:[
		{kind: "QueryBuilder"}
	],
});
enyo.kind({
	name: "QueryBuilder",
	kind: "FittableRows",
	components: [
		{kind: "Scroller", fit: true, components: [
			{name: "queryList", onSetupItem: "newQueryRow", kind: "Repeater", count: 1, components: [
				{kind: "QueryItem", onQueryValueChanged: "updateQuery"}
			]},
		]},
		{kind: "FittableColumns", components: [
			{kind: "onyx.Button", content: "Add Row", ontap: "addQueryRow"},
			{kind: "onyx.Button", content: "Remove Row", ontap: "removeQueryRow"},
			{kind: "onyx.Button", content: "log Query", ontap: "logQuery"},
		]}
	],

	logQuery: function(inSender, inEvent) {
		console.log(this.queryItems);
	},

	queryItems: [],

	newQueryRow: function(inSender, inEvent) {
		//console.log("QueryBuilder.newQueryRow",arguments, this.queryItems);
		item = inEvent.item.$.queryItem;
		item.setRowNumber(inEvent.index);
		if(inEvent.index >= this.queryItems.length) {
			this.queryItems[item.getRowNumber()] = item.getQueryValue();
		} else { 
			item.setQueryValue(this.queryItems[inEvent.index]);
		}
		return true;
	},

	addQueryRow: function(inSender, inEvent) {
		//console.log("QueryBuilder.addQueryRow",arguments);
		this.$.queryList.setCount(this.$.queryList.count + 1);
	},

	removeQueryRow: function(inSender, inEvent) {
		//console.log("QueryBuilder.removeQueryRow",arguments);
		this.queryItems.pop();
		this.$.queryList.setCount(this.$.queryList.count - 1);
	},
	
	updateQuery: function(inSender, inEvent) {
		//console.log("QueryBuilder.updateQuery",arguments);
		this.queryItems[inSender.getRowNumber()] = inSender.getQueryValue();
	},

	queries: {}
	
});

enyo.kind({
	name: "QueryItem",
	kind: "FittableColumns",
	published: {
		queryValue: [],
		rowNumber: -1,
	},
	events: {
		onQueryValueChanged:""
	},
	components: [
		{kind: "onyx.PickerDecorator", components: [
			{},
			{kind: "onyx.Picker", name: "queryType", onChange: "queryTypeSelected", components: [
				{content: "Start Date"},
				{content: "End Date"},
				{content: "Node Count"},
				{content: "Job Name"}
			]}
		]},
		//{kind: "FittableColumns", name: "queryDetails"},
		{kind: "FittableColumns", name: "startDateItems", showing: false, components: [
			{kind: "onyx.PickerDecorator", components: [
				{},
				{kind: "onyx.Picker", name: "startDateBeforeAfter", onChange: "startDateChanged", components: [
					{content:"Before", name: "startDateBefore"},
					{content:"After", name: "startDateAfter"}
				]}
			]},
			{kind: "onyx.PickerDecorator", components: [
				{},
				{kind: "onyx.Picker", onChange: "startDateChanged", name: "startMonth"}
			]},
			{kind: "onyx.PickerDecorator", components: [
				{},
				{kind: "onyx.Picker", onChange: "startDateChanged", name: "startDay"}
			]},
			{kind: "onyx.PickerDecorator", components: [
				{},
				{kind: "onyx.Picker", onChange: "startDateChanged", name: "startYear"}
			]},
		]},
		{kind: "FittableColumns", name: "endDateItems", showing: false, components: [
			{kind: "onyx.PickerDecorator", components: [
				{},
				{kind: "onyx.Picker", name: "endDateBeforeAfter", onChange: "endDateChanged", components: [
					{content:"Before", name: "endDateBefore"},
					{content:"After", name: "endDateAfter"}
				]}
			]},
			{kind: "onyx.PickerDecorator", components: [
				{},
				{kind: "onyx.Picker", onChange: "endDateChanged", name: "endMonth"}
			]},
			{kind: "onyx.PickerDecorator", components: [
				{},
				{kind: "onyx.Picker", onChange: "endDateChanged", name: "endDay"}
			]},
			{kind: "onyx.PickerDecorator", components: [
				{},
				{kind: "onyx.Picker", onChange: "endDateChanged", name: "endYear"}
			]},
		]},
		{kind: "FittableColumns", name: "nodeCountItems", showing: false, components: [
			{kind: "onyx.PickerDecorator", onChange: "nodeCountChanged", components: [
					{},
					{kind: "onyx.Picker", name: "nodeCountComparison", components: [
						{content: "<"},
						{content: ">"},
						{content: "=="},
						{content: "<="},
						{content: ">="}
					]}
				]},
				{kind: "onyx.InputDecorator", components: [
					{kind: "onyx.Input", name: "nodeCountNumber", oninput: "nodeCountChanged", placeholder: "Number of Nodes", type: "number"}
				]},
		]},
		{kind: "FittableColumns", showing: false, name: "jobNameItems", components: [
			{kind: "onyx.InputDecorator", components: [
				{kind: "onyx.Input", name: "jobName", oninput: "jobNameChanged"}
			]}
		]},
		
	],
	updatingQueryValue: false,
	activeControl: false,
	create: function() {
		this.inherited(arguments);
		months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
		for(i = 0; i < months.length; i++) {
			this.$.startMonth.createComponent({content: months[i]});
			this.$.endMonth.createComponent({content: months[i]});
		}
		for(i = 1; i <= 31; i++) {
			this.$.startDay.createComponent({content: i});
			this.$.endDay.createComponent({content: i});
		}
		for(i = 2005; i <= 2030; i++) {
			this.$.startYear.createComponent({content: i});
			this.$.endYear.createComponent({content: i});
		}
		this.render();
		this.setQueryValue(["Start Date"]);
	},
	queryTypeSelected: function(inSender, inEvent) {
		console.log("queryItem.queryTypeSelected", arguments, this.$.queryType, this.queryValue);
		if (this.$.queryType.selected.content != this.queryValue[0]) {
			this.setQueryValue([this.$.queryType.selected.content]);
		}
	},
	startDateChanged: function(inSender, inEvent) {
		//console.log("QueryItem.startDateChanged",arguments);
		if(!this.disableQueryValue) {
			beforeAfter = {"After": ">", "Before": "<"}[this.$.startDateBeforeAfter.selected.content]
			this.queryValue = [	this.$.queryType.selected.content,
						beforeAfter,
						this.$.startMonth.selected.content,
						this.$.startDay.selected.content,
						this.$.startYear.selected.content];
			this.doQueryValueChanged();
		}
	},
	endDateChanged: function(inSender, inEvent) {
		//console.log("QueryItem.endDateChanged",arguments);
		if(!this.disableQueryValue) {
			beforeAfter = {"After": ">", "Before": "<"}[this.$.endDateBeforeAfter.selected.content]
			this.queryValue = [	this.$.queryType.selected.content,
						beforeAfter,
						this.$.endMonth.selected.content,
						this.$.endDay.selected.content,
						this.$.endYear.selected.content];
			this.doQueryValueChanged();
		}
	},
	nodeCountChanged: function(inSender, inEvent) {
		//console.log("QueryItem.nodeCountChanged",arguments);
		if(!this.disableQueryValue) {
			this.queryValue = [	this.$.queryType.selected.content,
						this.$.nodeCountComparison.selected.content,
						this.$.nodeCountNumber.getValue()];
			this.doQueryValueChanged();
		}
	},
	jobNameChanged: function(inSender, inEvent) {
		//console.log("QueryItem.nodeNameChanged",arguments);
		if(!this.disableQueryValue) {
			this.queryValue = [	this.$.queryType.selected.content,
						this.$.jobName.getValue()];
			this.doQueryValueChanged();
		}
	},
	queryValueChanged: function(oldValue) {
		//console.log("QueryItem.queryValueChanged", arguments, this.queryValue);
		this.disableQueryValue = true
		components = this.$.queryType.getControls();
		for(i=0;i<components.length;i++) {
			if(components[i].content == this.queryValue[0]) {
				this.$.queryType.setSelected(components[i]);
			}
		}
		if(this.activeControl != false) {
			this.activeControl.setShowing(false);
		}
		switch(this.queryValue[0]) {
			case "Start Date":
				this.activeControl = this.$.startDateItems;
				if(this.queryValue.length < 5) {
					this.queryValue = [this.queryValue[0], "<", "Jan", 1, 2012];
				}
				console.log(this.queryValue[2], {"<": "Before", ">": "After"}[this.queryValue[1]]);
				this.setPickerWithText(this.$.startDateBeforeAfter, {"<": "Before", ">": "After"}[this.queryValue[1]]);
				this.setPickerWithText(this.$.startMonth, this.queryValue[2]);
				this.setPickerWithText(this.$.startDay, this.queryValue[3]);
				this.setPickerWithText(this.$.startYear, this.queryValue[4]);
				break;
			case "End Date":
				this.activeControl = this.$.endDateItems;
				if(this.queryValue.length < 5) {
					this.queryValue = [this.queryValue[0], "<", "Jan", 1, 2013];
				}
				console.log(this.queryValue[2], {"<": "Before", ">": "After"}[this.queryValue[1]]);
				this.setPickerWithText(this.$.endDateBeforeAfter, {"<": "Before", ">": "After"}[this.queryValue[1]]);
				this.setPickerWithText(this.$.endMonth, this.queryValue[2]);
				this.setPickerWithText(this.$.endDay, this.queryValue[3]);
				this.setPickerWithText(this.$.endYear, this.queryValue[4]);
				break;
			case "Node Count":
				this.activeControl = this.$.nodeCountItems;
				if(this.queryValue.length < 3) {
					this.queryValue = [this.queryValue[0], "<"];
				}
				this.setPickerWithText(this.$.nodeCountComparison, this.queryValue[1]);
				this.$.nodeCountNumber.setValue(this.queryValue[2]);
				break;
			case "Job Name":
				this.activeControl = this.$.jobNameItems;
				if(this.queryValue.length > 1) {
					console.log("Setting ", this.$.jobName, "to", this.queryValue[1]);
					this.$.jobName.setValue(this.queryValue[1]);
				}
				break;
		}
		this.activeControl.setShowing(true);
		this.disableQueryValue = false;
	},
	setPickerWithText: function(component, selectText) {
		components = component.getControls();
		for(i = 0; i < components.length; i++) {
			if(components[i].content == selectText) {
				component.setSelected(components[i]);
			}
		}
	}
});
