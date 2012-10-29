enyo.kind({
	name: "JobView",
	kind: "FittableRows",
	classes: "JobView",
	published: {
		job: false,
	},
	events: {
		onJobViewClosed: "",
	},
	components:[
		{kind: "FittableColumns", fit: true, components: [
			{kind: "Scroller", fit: true, components: [
				{name: "spinnerPopup", kind: "onyx.Popup", centered: true, floating: true, components: [
					{kind: "onyx.Spinner"}
				]},
				{name: "jobGraphs"},
			]},
			{kind: "FittableRows", components: [
				{kind: "FittableColumns", components: [
					{components: [
						{kind: "Checkbox", showing: false},
					]},
					{name: "averageDisplay"},
				]},
				{kind: "FittableColumns", components: [
					{components: [
						{kind: "Checkbox", showing: false},
					]},
					{name: "sumDisplay"},
				]},
				{kind: "Scroller", classes: "legend", name: "legendScroller", fit: true, components: [
					{kind: "FittableColumns", components: [
						{components: [
							{kind: "Checkbox", onActivate: "toggleCheckboxes", active: true},
						]},
						{content: "Select All"},
					]},
					{kind: "Repeater", name: "legend", onSetupItem: "legendItem", components: [
						{kind: "FittableColumns", components: [
							{components: [
								{name: "enable", kind: "Checkbox", onActivate: "legendChecked", host: ""},
							]},
							{classes: "color-border", components: [
								{name: "color"},
							]},
							{name: "label", classes: "legend-label"},
							{name: "value", classes: "legend-label"},
						]},
					]},
				]},
			]},
		]},
		{kind: "onyx.Toolbar", components: [
			{kind: "onyx.Button", ontap: "doJobViewClosed", content: "Close"},
			{kind: "onyx.Button", show: false, name: "cviewButton", ontap: "downloadCview", content: "Download Cview"},
		]},
	],
	downloadCview: function(inSender, inEvent) {
		window.location.href = this.job.cview;
	},
	toggleCheckboxes: function(inSender, inEvent) {
		this.legendUpdatesEnabled = false;
		for(i=0;i<this.legend.length;i++) {
			this.legend[i].enabled = inSender.checked;
		}
		for(i=0;i<this.graphs.length;i++) {
			this.graphs[i].setLegend(this.legend.slice(0));
		}
		this.$.legend.setCount(this.legend.length);
		this.legendUpdatesEnabled = true;
	},
	legendUpdatesEnabled: true,
	legendChecked: function(inSender, inEvent) {
		if(this.legendUpdatesEnabled) {
			for(i=0;i<this.legend.length;i++) {
				if(this.legend[i].host == inSender.host) {
					this.legend[i].enabled = inSender.checked;
					break;
				}
			}
			this.values[inSender.host].setContent("");
			this.updateLegendValues()
			for(i=0;i<this.graphs.length;i++) {
				this.graphs[i].setLegend(this.legend.slice(0));
			}
		}
	},
	values: {},
	legendItem: function(inSender, inEvent) {
		item = this.legend[inEvent.index];
		inEvent.item.$.enable.checked = item.enabled;
		inEvent.item.$.enable.host = item.host
		inEvent.item.$.color.setStyle("border: 5px solid hsl("+item.color[0]+", "+(item.color[1]*100)+"%, "+(item.color[2]*100)+"%);");
		inEvent.item.$.label.setContent(item.host);
		this.values[item.host] = inEvent.item.$.value;
		return true;
	},
	updateLegendValues: function(inSender, inEvent) {
		sum = 0;
		count = 0;
		for(host in inEvent) {
			if(host != "originator") {
				this.values[host].setContent(": " + inEvent[host].toPrecision(4));
				sum += inEvent[host];
				count++;
			}
		}
		if(count > 0) {
			this.$.averageDisplay.setContent("Average: " + (sum/count).toPrecision(4));
			this.$.sumDisplay.setContent("Sum: " + sum.toPrecision(4));
		}
	},
	spin: function() {
		this.$.jobGraphs.destroyClientControls();
		this.$.spinnerPopup.show();
	},
	legend: [],
	graphs: [],
	jobChanged: function(oldValue) {
		//this.$.jobGraphs.destroyClientControls();
		this.graphs = [];
		this.values = {};
		//this.$.jobGraphs.render();
		if(this.job.cview) {
			this.$.cviewButton.setShowing(true);
		} else {
			this.$.cviewButton.setShowing(false);
		}
		length = 0;
		if(this.job["version"] == 2) {
			this.legend = [];
			numHosts = this.job["hosts"].length;
			hue = hueFractions = 350/numHosts;
			lightnessFractions = .3/numHosts;
			lightness = .3;
			for(host in this.job["hosts"]) {
				hue += hueFractions;
				lightness += lightnessFractions;
				this.legend[host] = {host: this.job["hosts"][host], color: [hue, 1, lightness], enabled: true};
			}
			this.$.legend.setCount(numHosts);
			this.$.legendScroller.setShowing(true);
		} else {
			this.$.legendScroller.setShowing(false);
		}
		for(group in this.job["graphs"]) {
			length++;
			if(group == "") {
				groupHeader = this.$.jobGraphs.createComponent({content: "other", ontap: "toggleDrawer", classes: "group-header"}, {owner:  this});
			} else {
				groupHeader = this.$.jobGraphs.createComponent({content: group, ontap: "toggleDrawer", classes: "group-header"}, {owner:  this});
			}
			groupDrawer = this.$.jobGraphs.createComponent({kind: "onyx.Drawer", open: false});
			groupHeader.drawer = groupDrawer;
			for(metric in this.job["graphs"][group]) {
				if(this.job["graphs"][group][metric]["unit"] != null)
					unit = " ("+this.job["graphs"][group][metric]["unit"]+")";
				else
					unit = "";
				
				if(this.job["graphs"][group][metric]["description"] != null)
					description = " - " + this.job["graphs"][group][metric]["description"];
				else
					description = "";
				headerText = 	this.job["graphs"][group][metric]["name"]
						+ unit
						+ description;
				metricHeader = groupDrawer.createComponent({content: headerText, ontap: "toggleDrawer", classes: "image-header"}, {owner:  this})
				metricDrawer = groupDrawer.createComponent({kind: "onyx.Drawer", open: false});
				metricHeader.drawer = metricDrawer;
				if(this.job["version"] == 1) {
					metricDrawer.createComponent({kind: "Image", src: this.job["graphs"][group][metric]["src"], ontap: "toggleThumbnail", classes: "thumbnail", thumbnail: true}, {owner: this});
				} else {
					this.graphs.push( metricDrawer.createComponent({kind: "Flot", legend: this.legend, src: this.job["graphs"][group][metric]["src"], classes: "graph", onValuesUpdate: "updateLegendValues"}, {owner: this}));
				}
			}
		}
		if(length == 0) {
			this.$.jobGraphs.createComponent({content: "Sorry there is no data for this job", classes:"job-error"});
		}
		this.$.spinnerPopup.hide();
		this.$.jobGraphs.render();
	},
	toggleDrawer: function(inSender, inEvent) {
		if(inSender.drawer.getOpen()) {
			inSender.drawer.setOpen(0);
			if(inSender.getClasses().indexOf("group-header") != -1)
				inSender.setClasses("group-header");
		} else {
			components = inSender.drawer.getControls();
			for(comp in components) {
				if(components[comp].kind == "Flot") {
					components[comp].plot();
				}
			}
			if(inSender.getClasses().indexOf("group-header") != -1)
				inSender.setClasses("group-header group-header-act");
			inSender.drawer.setOpen(1);
		}
	},
	toggleThumbnail: function(inSender, inEvent) {
		inSender.thumbnail = !inSender.thumbnail;
		inSender.addRemoveClass("thumbnail", inSender.thumbnail);
	},
});
