enyo.kind({
	name: "App",
	fit: true,
	kind: "Panels",
	components:[
		{kind: "QueryBuilder"}
		//{name: "hello", content: "Hello World", allowHtml: true, ontap: "helloWorldTap"}
	],
	helloWorldTap: function(inSender, inEvent) {
		this.$.hello.addContent("<br/><b>hello</b> control was tapped. This was a test");
	}
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
			{kind: "onyx.Button", content: "Remove Row", ontap: "removeQueryRow"}
		]}
	],

	queryItems: [],

	newQueryRow: function(inSender, inEvent) {
		//console.log(this.queryItems);
		//console.log(inEvent.index);
		item = inEvent.item.$.queryItem;
		if(inEvent.index >= this.queryItems.length) {
			this.queryItems.push(item.getQueryValue());
		} else { 
			item.setQueryValue(this.queryItems[inEvent.index].slice());
		}
		item.setRowNumber(inEvent.index);
		return true;
	},

	addQueryRow: function(inSender, inEvent) {
		this.$.queryList.setCount(this.$.queryList.count + 1);
	},

	removeQueryRow: function(inSender, inEvent) {
		this.$.queryList.setCount(this.$.queryList.count - 1);
	},
	
	updateQuery: function(inSender, inEvent) {
		this.queryItems[inSender.getRowNumber()] = inSender.getQueryValue();
		console.log(this.queryItems);
	},

	queries: {}
	
});

enyo.kind({
	name: "QueryItem",
	kind: "FittableColumns",
	published: {
		queryValue: false,
		rowNumber: -1,
	},
	events: {
		onQueryValueChanged:""
	},
	setNodeCount: function(inSender, inEvent) {
		//console.log(this.$.queryType.components[1].setSelected(this.$.queryType.components[1].components[2]));
		//this.$.queryType.render();
		//console.log(this.$.queryType);
		//console.log(this.$.nodeCount);
		//console.log(this.$.queryType.getSelected());
		//this.$.queryType.setSelected(this.$.queryType.components[2]);
		//console.log(this.$.StartDateItems);
	},
	components: [
		//{kind: "onyx.Button", ontap: "setNodeCount"},
		{kind: "onyx.PickerDecorator", components: [
			{},
			{kind: "onyx.Picker", name: "queryType", onChange: "queryTypeSelected", components: [
				{content: "Start Date", active: true},
				{content: "End Date"},
				{content: "Node Count", name: "nodeCount"},
				{content: "Job Name"}
			]}
		]},
		{kind: "FittableColumns", name: "queryDetails"},
		{kind: "FittableColumns", showing: true, name: "StartDateItems", components: [
/*
			{kind: "onyx.PickerDecorator", onChange: "startDateChanged", components: [
				{},
				{kind: "onyx.Picker", name: "startBeforeAfter", components: [
					{content: "Before"},
					{content: "After", active: true}
				]}
			]},
			{kind: "onyx.PickerDecorator", onChange: "startDateChanged", components: [
				{},
				{kind: "onyx.Picker", name: "startMonth", components: [
					{content: "Jan", active: true},
					{content: "Feb"},
					{content: "Mar"},
					{content: "Apr"},
					{content: "May"},
					{content: "Jun"},
					{content: "Jul"},
					{content: "Aug"},
					{content: "Sep"},
					{content: "Oct"},
					{content: "Nov"},
					{content: "Dec"}
				]}
			]}
*/
		]},
		{kind: "FittableColumns", showing: false, name: "EndDateItems", components: [
			{kind: "onyx.PickerDecorator", onChange: "endDateChanged", components: [
				{},
				{kind: "onyx.Picker", components: [
					{content: "Before", active: true},
					{content: "After"}
				]}
			]},
			{kind: "onyx.PickerDecorator", onChange: "endDateChanged", components: [
				{},
				{kind: "onyx.Picker", components: [
					{content: "Jan", active: true},
					{content: "Feb"},
					{content: "Mar"},
					{content: "Apr"},
					{content: "May"},
					{content: "Jun"},
					{content: "Jul"},
					{content: "Aug"},
					{content: "Sep"},
					{content: "Oct"},
					{content: "Nov"},
					{content: "Dec"}
				]}
			]}
		]},
		{kind: "FittableColumns", showing: false, name: "NodeCountItems", components: [
			{kind: "onyx.PickerDecorator", onChange: "nodeCountChanged", components: [
				{},
				{kind: "onyx.Picker", components: [
					{content: "<", active: true},
					{content: ">"},
					{content: "=="},
					{content: ">="},
					{content: ">="}
				]}
			]},
			{kind: "onyx.InputDecorator", components: [
				{kind: "onyx.Input", oninput: "nodeCountChanged", placeholder: "Number of Nodes"}
			]}
		]},
		{kind: "FittableColumns", showing: false, name: "JobNameItems", components: [
			{kind: "onyx.InputDecorator", components: [
				{kind: "onyx.Input", oninput: "nodeCountChanged", placeholder: "Job Name"}
			]}
		]},
		
	],
	create: function() {
		this.inherited(arguments);
		this.setQueryValue(["StartDate", ">", "Jan", "1", "2012"]);
	},
	queryTypeSelected: function(inSender, inEvent) {
/*
		this.activeItem.hide();
		this.activeItem = {	"Start Date": this.$.StartDateItems,
					"End Date": this.$.EndDateItems,
					"Node Count": this.$.NodeCountItems,
					"Job Name": this.$.JobNameItems}[inEvent.content];
		this.activeItem.show();
*/
	},
	startDateChanged: function(inSender, inEvent) {
		console.log("startDateChanged");
		//console.log(inSender);
		//console.log(inEvent);
		components = [this.$.beforeAfter, this.$.startMonth];//, this.$.startDay, this.$.startYear];
		for(i = 0;i < components.length;i++) {
			if(! components[i] || ! components[i].selected) {
				return;
			}
		}
		//console.log(this);
		beforeAfter = {"After": ">", "Before": "<"}[this.$.beforeAfter.selected.content]
		this.setQueryValue = ["startDate", beforeAfter, this.$.startMonth.selected.content];//, this.$.startDay.selected.content, this.$.startYear.selected.content];
		this.doQueryValueChanged();
/*
		console.log(this.queryValue);
*/
	},
	queryValueChanged: function(oldValue) {
		this.$.queryDetails.destroyClientControls();
		//console.log(oldValue);
		console.log("queryValueChanged", this.queryValue);
		switch(this.queryValue[0]) {
			case "StartDate":
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
/*
				startDay = this.$.queryDetails.createComponent({kind: "onyx.PickerDecorator", components: [{},{kind: "onyx.Picker", onChange: "startDateChanged", name: "startDay"}]}, {owner: this}).getClientControls()[1];;
				for(i = 1; i <= 31; i++) {
					startDay.createComponent({content: i, active: i == this.queryValue[3]});
				}
				startYear = this.$.queryDetails.createComponent({kind: "onyx.PickerDecorator", components: [{},{kind: "onyx.Picker", onChange: "startDateChanged", name: "startYear"}]}, {owner: this}).getClientControls()[1];;
				for(i = 2005; i <= 2030; i++) {
					startYear.createComponent({content: i, active: i == this.queryValue[4]});
				}
*/
				break;
		}
		this.$.queryDetails.render();
		//console.log(this);
	},
/*
	setQueryValue: function(newValue) {
		console.log("setQueryValue");
		tmp = this.queryValue;
		this.queryValue = newValue;
		this.queryValueChanged(tmp);
	}
*/
});
