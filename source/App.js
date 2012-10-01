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
		{kind: "FittableColumns", name: "queryDetails"},
		{kind: "FittableColumns", showing: false, name: "JobNameItems", components: [
			{kind: "onyx.InputDecorator", components: [
				{kind: "onyx.Input", oninput: "nodeCountChanged", placeholder: "Job Name"}
			]}
		]},
		
	],
	disableQueryValueEvent: false,
	create: function() {
		this.inherited(arguments);
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
		components = [this.$.beforeAfter, this.$.startMonth, this.$.startDay, this.$.startYear];
		for(i = 0;i < components.length;i++) {
			if(! components[i] || ! components[i].selected) {
				return;
			}
		}
		beforeAfter = {"After": ">", "Before": "<"}[this.$.beforeAfter.selected.content]
		this.queryValue = ["Start Date", beforeAfter, this.$.startMonth.selected.content, this.$.startDay.selected.content, this.$.startYear.selected.content];
		if(!this.disableQueryValueEvent) {
			this.doQueryValueChanged();
		}
	},
	endDateChanged: function(inSender, inEvent) {
		//console.log("QueryItem.endDateChanged",arguments);
		components = [this.$.beforeAfter, this.$.endMonth, this.$.endDay, this.$.endYear];
		for(i = 0;i < components.length;i++) {
			if(! components[i] || ! components[i].selected) {
				return;
			}
		}
		beforeAfter = {"After": ">", "Before": "<"}[this.$.beforeAfter.selected.content]
		this.queryValue = ["End Date", beforeAfter, this.$.endMonth.selected.content, this.$.endDay.selected.content, this.$.endYear.selected.content];
		if(!this.disableQueryValueEvent) {
			this.doQueryValueChanged();
		}
	},
	nodeCountChanged: function(inSender, inEvent) {
		//console.log("QueryItem.nodeCountChanged",arguments);
		if(! this.$.comparison || ! this.$.comparison.selected) {
			return;
		}
		if(! this.$.nodeCount ) {
			return;
		}
		this.queryValue = ["Node Count", this.$.comparison.selected.content, this.$.nodeCount.getValue()];
		//console.log("nodecount:", this.$.nodeCount);
		if(!this.disableQueryValueEvent) {
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
		this.$.queryDetails.destroyClientControls();
		switch(this.queryValue[0]) {
			case "Start Date":
				if(this.queryValue.length < 5) {
					this.queryValue = [this.queryValue[0], "<", "Jan", "1", "2012"];
				}
				this.$.queryDetails.createComponent({	kind: "onyx.PickerDecorator", 
									components: [
										{},
										{ kind: "onyx.Picker", name: "beforeAfter", onChange: "startDateChanged", components: [
											{content:"Before", active: this.queryValue[1] == "<"},
											{content:"After", active: this.queryValue[1] == ">"}
										]}
				]}, {owner: this});
				startMonth = this.$.queryDetails.createComponent({kind: "onyx.PickerDecorator", components: [{},{kind: "onyx.Picker", onChange: "startDateChanged", name: "startMonth"}]}, {owner: this}).getClientControls()[1];
				months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
				for(i = 0; i < months.length; i++) {
					startMonth.createComponent({content: months[i], active: months[i] == this.queryValue[2]});
				}
				startDay = this.$.queryDetails.createComponent({kind: "onyx.PickerDecorator", components: [{},{kind: "onyx.Picker", onChange: "startDateChanged", name: "startDay"}]}, {owner: this}).getClientControls()[1];;
				for(i = 1; i <= 31; i++) {
					startDay.createComponent({content: i, active: i == this.queryValue[3]});
				}
				startYear = this.$.queryDetails.createComponent({kind: "onyx.PickerDecorator", components: [{},{kind: "onyx.Picker", onChange: "startDateChanged", name: "startYear"}]}, {owner: this}).getClientControls()[1];;
				for(i = 2005; i <= 2030; i++) {
					startYear.createComponent({content: i, active: i == this.queryValue[4]});
				}
				break;
			case "End Date":
				if(this.queryValue.length < 5) {
					this.queryValue = [this.queryValue[0], "<", "Jan", "1", "2013"];
				}
				this.$.queryDetails.createComponent({	kind: "onyx.PickerDecorator", 
									components: [
										{},
										{ kind: "onyx.Picker", name: "beforeAfter", onChange: "endDateChanged", components: [
											{content:"Before", active: this.queryValue[1] == "<"},
											{content:"After", active: this.queryValue[1] == ">"}
										]}
				]}, {owner: this});
				endMonth = this.$.queryDetails.createComponent({kind: "onyx.PickerDecorator", components: [{},{kind: "onyx.Picker", onChange: "endDateChanged", name: "endMonth"}]}, {owner: this}).getClientControls()[1];
				months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
				for(i = 0; i < months.length; i++) {
					endMonth.createComponent({content: months[i], active: months[i] == this.queryValue[2]});
				}
				endDay = this.$.queryDetails.createComponent({kind: "onyx.PickerDecorator", components: [{},{kind: "onyx.Picker", onChange: "endDateChanged", name: "endDay"}]}, {owner: this}).getClientControls()[1];;
				for(i = 1; i <= 31; i++) {
					endDay.createComponent({content: i, active: i == this.queryValue[3]});
				}
				endYear = this.$.queryDetails.createComponent({kind: "onyx.PickerDecorator", components: [{},{kind: "onyx.Picker", onChange: "endDateChanged", name: "endYear"}]}, {owner: this}).getClientControls()[1];;
				for(i = 2005; i <= 2030; i++) {
					endYear.createComponent({content: i, active: i == this.queryValue[4]});
				}
				break;
			case "Node Count":
				if(this.queryValue.length < 3) {
					this.queryValue = [this.queryValue[0], "<"];
				}
				this.$.queryDetails.createComponent({kind: "onyx.PickerDecorator", onChange: "nodeCountChanged", components: [
					{},
					{kind: "onyx.Picker", name: "comparison", components: [
						{content: "<", active: this.queryValue[1] == "<"},
						{content: ">", active: this.queryValue[1] == ">"},
						{content: "==", active: this.queryValue[1] == "=="},
						{content: "<=", active: this.queryValue[1] == "<="},
						{content: ">=", active: this.queryValue[1] == ">="}
					]}
				]}, {owner: this});
				this.$.queryDetails.createComponent({kind: "onyx.InputDecorator", components: [{kind: "onyx.Input", name: "nodeCount", oninput: "nodeCountChanged", content: this.queryValue[2], placeholder: "Number of Nodes"}]}, {owner: this});
				break;
		}
		this.$.queryDetails.render();
		this.disableQueryValue = false;
	},
});
