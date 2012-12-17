enyo.kind({
	name: "AdminInterface",
	kind: "onyx.Popup",
	classes: "admin-interface",
	components:[
		{kind: "MetricManager", name: "metricManager", onNewMetricList: "updateMetrics"},
		{kind: "SettingManager", name: "settingManager", onNewSettingList: "updateSettings"},
		{kind: "FittableRows", style: "width: 100%; height: 100%;", components: [
			{kind: "onyx.Toolbar", components: [
				{kind: "onyx.Button", content: "Metrics", panel: 0, classes: "admin-active-button", ontap: "changeAdminPanel"},
				{kind: "onyx.Button", content: "Settings", panel: 1, ontap: "changeAdminPanel"}
			]},
			{kind: "Panels", name: "adminPanel", fit: true, components: [
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
				]},
				{kind: "FittableRows", components: [
					{kind: "Scroller", fit: true, components: [
						{kind: "Repeater", name: "settingList", onSetupItem: "newSettingRow", components: [
							{name: "description", classes: "admin-description"},
							{kind: "FittableColumns", classes: "admin-row", components: [
								{name: "label", style: "width: 20%", classes: "admin-label"},
								{fit: true, components: [
									{kind: "onyx.InputDecorator", style: "width: 50%", name: "stringValueDecorator", components: [
										{kind: "onyx.Input", style: "width: 100%", name: "stringValue", onchange: "settingUpdated"}
									]},
									{kind: "onyx.InputDecorator", style: "width: 50%", name: "passwordValueDecorator", components: [
										{kind: "onyx.Input", style: "width: 100%", name: "passwordValue", type: "password", onchange: "settingUpdated"}
									]},
									{kind: "onyx.PickerDecorator", name: "pickerValueDecorator", components: [
										{},
										{kind: "onyx.Picker", name: "pickerValue", onChange:"settingUpdated"}
									]}
								]}
							]}
						]}
					]}
				]}
			]},
			{kind: "onyx.Toolbar", components: [
				{kind: "onyx.Button", name: "close", content: "Close", classes: "admin-close-button", ontap: "closeAdmin"}
			]}
		]}
	],
	changeAdminPanel: function(inSender, inEvent) {
		var buttons = inSender.parent.children;
		for(var i=0;i<buttons.length;i++) {
			buttons[i].removeClass("admin-active-button");
		}
		inSender.addClass("admin-active-button");
		this.$.adminPanel.setIndex(inSender.panel);
	},
	showSettings: function(inSender, inEvent) {
		this.$.adminPanel.setIndex(1);
	},
	updateValues: function() {
		this.$.metricManager.getMetricList();
		this.$.settingManager.getSettingList();
	},
	settings: false,
	updateSettings: function(inSender, inResponse) {
		this.settings = inResponse;
		this.settings.sort(function(a,b) {
			if(a.id > b.id)
				return 1;
			else 
				return -1;
		});
		this.$.settingList.setCount(inResponse.length);
	},
	newSettingRow: function(inSender, inEvent) {
		inEvent.item.$.label.setContent(this.settings[inEvent.index].label);
		if(typeof this.settings[inEvent.index].description != "undefined")
			inEvent.item.$.description.setContent(this.settings[inEvent.index].description);
		else
			inEvent.item.$.description.setShowing(false);
			
		if(this.settings[inEvent.index].type == "string" || this.settings[inEvent.index].type == "integer") {
			inEvent.item.$.stringValue.setValue(this.settings[inEvent.index].value);
			inEvent.item.$.stringValueDecorator.setShowing(true);
			inEvent.item.$.passwordValueDecorator.setShowing(false);
			inEvent.item.$.pickerValueDecorator.setShowing(false);
		} else if(this.settings[inEvent.index].type == "password") {
			inEvent.item.$.passwordValue.setValue(this.settings[inEvent.index].value);
			inEvent.item.$.passwordValueDecorator.setShowing(true);
			inEvent.item.$.stringValueDecorator.setShowing(false);
			inEvent.item.$.pickerValueDecorator.setShowing(false);
		} else if(this.settings[inEvent.index].type == "list") {
			inEvent.item.$.pickerValue.destroyClientControls();
			for(var i=0;i<this.settings[inEvent.index].values.length;i++) {
				var newComponent = {content: this.settings[inEvent.index].values[i]};
				newComponent.active = this.settings[inEvent.index].values[i] == this.settings[inEvent.index].value;
				inEvent.item.$.pickerValue.createComponent(newComponent);
			}
			inEvent.item.$.pickerValueDecorator.setShowing(true);
			inEvent.item.$.stringValueDecorator.setShowing(false);
			inEvent.item.$.passwordValueDecorator.setShowing(false);
		}
			
	},
	settingUpdated: function(inSender, inEvent) {
		var settingId = this.settings[inEvent.index].id;
		if(inSender.kind == "onyx.Picker") {
			newValue = inEvent.content;
		} else {
			newValue = inSender.getValue();
		}
		if(newValue != this.settings[inEvent.index].value) {
			this.settings[inEvent.index].value = newValue;
			this.$.settingManager.updateSetting(settingId, this.settings[inEvent.index].value);
		}
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
		var metric = {	"name": this.$.newName.getValue(),
				"unit": this.$.newUnit.getValue(),
				"group": this.$.newGroup.getValue(),
				"description": this.$.newDescription.getValue()};
		this.$.metricManager.updateMetric("", metric);
		this.$.metricManager.getMetricList();
	},
	metricUpdated: function(inSender, inEvent) {
		var metricName = this.metrics[inEvent.index].name;
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
