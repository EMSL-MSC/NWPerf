enyo.kind({
	name: "AdminInterface",
	kind: "onyx.Popup",
	classes: "admin-interface",
	components:[
		{kind: "MetricManager", name: "metricManager", onNewMetricList: "updateMetrics"},
		{kind: "FittableRows", style: "width: 100%; height: 100%;", components: [
			{kind: "onyx.Toolbar", components: [
				{kind: "onyx.Button", content: "Metrics", ontap: "closeAdmin"}
			]},
			{kind: "Panels", fit: true, components: [
				{kind: "FittableRows", components: [
					{kind: "FittableColumns", components: [
						{style: "margin: 1px; width: 28%;", content: "Name"},
						{style: "margin: 1px; width: 14%;", content: "Units"},
						{style: "margin: 1px; width: 14%;", content: "Group"},
						{style: "margin: 1px; width: 38%;", content: "Description"},
					]},
					{kind: "Scroller", fit: true, components: [
						{kind: "Repeater", name: "metricList", onSetupItem: "newMetricRow", components: [
							{kind: "FittableColumns", components: [
								{style: "margin: 2px; width: 28%;", kind: "onyx.InputDecorator", components: [
									{style: "width: 100%;", kind: "onyx.Input", name: "name", onchange: "metricUpdated"}
								]},
								{style: "margin: 2px; width: 14%;", kind: "onyx.InputDecorator", components: [
									{style: "width: 100%;", kind: "onyx.Input", name: "unit", onchange: "metricUpdated"}
								]},
								{style: "margin: 2px; width: 14%;", kind: "onyx.InputDecorator", components: [
									{style: "width: 100%;", kind: "onyx.Input", name: "group", onchange: "metricUpdated"}
								]},
								{style: "margin: 2px; width: 38%;", kind: "onyx.InputDecorator", components: [
									{style: "width: 100%;", kind: "onyx.Input", name: "description", onchange: "metricUpdated"}
								]},
								{style: "min-width: 30px;", kind: "onyx.Button", ontap: "deleteMetric", content: "-"}
							]}
						]},
						{kind: "FittableColumns", components: [
							{style: "margin: 2px; width: 28%;", kind: "onyx.InputDecorator", components: [
								{style: "width: 100%;", kind: "onyx.Input", name: "newName", onchange: "metricAdded", placeholder: "New Metric Name"}
							]},
							{style: "margin: 2px; width: 14%;", kind: "onyx.InputDecorator", components: [
								{style: "width: 100%;", kind: "onyx.Input", name: "newUnit", onchange: "metricAdded", placeholder: "New Unit"}
							]},
							{style: "margin: 2px; width: 14%;", kind: "onyx.InputDecorator", components: [
								{style: "width: 100%;", kind: "onyx.Input", name: "newGroup", onchange: "metricAdded", placeholder: "New Group"}
							]},
							{style: "margin: 2px; width: 38%;", kind: "onyx.InputDecorator", components: [
								{style: "width: 100%;", kind: "onyx.Input", name: "newDescription", onchange: "metricAdded", placeholder: "New Description"}
							]},
						]}
					]}
				]}
			]},
			{kind: "onyx.Toolbar", components: [
				{kind: "onyx.Button", name: "close", content: "Close", classes: "admin-close-button", ontap: "closeAdmin"}
			]}
		]}
	],
	updateValues: function() {
		this.$.metricManager.getMetricList();
	},
	metrics: false,
	updateMetrics: function(inSender, inResponse) {
		this.metrics = inResponse;
		this.metrics.sort(function(a,b) {
			if(a.name > b.name)
				return 1;
			else 
				return -1;
		});
		this.$.metricList.setCount(inResponse.length);
	},
	newMetricRow: function(inSender, inEvent) {
		inEvent.item.$.name.setValue(this.metrics[inEvent.index].name);
		inEvent.item.$.unit.setValue(this.metrics[inEvent.index].unit);
		inEvent.item.$.group.setValue(this.metrics[inEvent.index].group);
		inEvent.item.$.description.setValue(this.metrics[inEvent.index].description);
	},
	metricAdded: function(inSender, inEvent) {
		if(this.$.newName.getValue() == "")
			return true;
		metric = {	"name": this.$.newName.getValue(),
				"unit": this.$.newUnit.getValue(),
				"group": this.$.newGroup.getValue(),
				"description": this.$.newDescription.getValue()};
		this.$.metricManager.updateMetric("", metric);
		this.$.metricManager.getMetricList();
	},
	metricUpdated: function(inSender, inEvent) {
		metricName = this.metrics[inEvent.index].name;
		this.metrics[inEvent.index][inSender.name] = inSender.getValue();
		this.$.metricManager.updateMetric(metricName, this.metrics[inEvent.index]);
	},
	deleteMetric: function(inSender, inEvent) {
		this.$.metricManager.deleteMetric(this.metrics[inEvent.index].name);
		this.metrics.splice(inEvent.index,1);
		this.$.metricList.setCount(this.metrics.length);
	},
	closeAdmin: function(inSender, inEvent) {
		this.updateValues();
		this.hide();
	}
});
