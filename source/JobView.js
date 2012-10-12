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
		{kind: "Scroller", fit: true, components: [
			{name: "jobGraphs"},
		]},
		{kind: "onyx.Toolbar", components: [
			{kind: "onyx.Button", ontap: "doJobViewClosed", content: "Close"},
		]},
	],
	spin: function() {
		this.$.jobGraphs.destroyClientControls();
		this.$.jobGraphs.createComponent({style:"background:black; border-radius:5px; padding:15px; width:65px;", components: [
			{kind: "onyx.Spinner"}
		]});
		this.$.jobGraphs.render();
	},
	jobChanged: function(oldValue) {
		console.log("jobChanged", this.job);
		this.$.jobGraphs.destroyClientControls();
		this.$.jobGraphs.render();
		if(this.job["version"] = 1) {
			length = 0;
			for(group in this.job["graphs"]) {
				console.log(group);
				length++;
				groupHeader = this.$.jobGraphs.createComponent({content: group, ontap: "toggleDrawer", classes: "group-header"}, {owner:  this});
				groupDrawer = this.$.jobGraphs.createComponent({kind: "onyx.Drawer", open: false});
				groupHeader.drawer = groupDrawer;
				for(metric in this.job["graphs"][group]) {
					headerText = this.job["graphs"][group][metric]["name"]+" - "+ this.job["graphs"][group][metric]["description"];
					metricHeader = groupDrawer.createComponent({content: headerText, ontap: "toggleDrawer", classes: "image-header"}, {owner:  this})
					metricDrawer = groupDrawer.createComponent({kind: "onyx.Drawer", open: false});
					metricHeader.drawer = metricDrawer;
					metricDrawer.createComponent({kind: "Image", src: this.job["graphs"][group][metric]["src"], ontap: "toggleThumbnail", classes: "thumbnail", thumbnail: true}, {owner: this});
				}
			}
			if(length == 0) {
				this.$.jobGraphs.createComponent({content: "Sorry there is no data for this job", classes:"job-error"});
			}
		}
		this.$.jobGraphs.render();
	},
	toggleDrawer: function(inSender, inEvent) {
		inSender.drawer.setOpen(! inSender.drawer.getOpen());
	},
	toggleThumbnail: function(inSender, inEvent) {
		inSender.thumbnail = !inSender.thumbnail;
		inSender.addRemoveClass("thumbnail", inSender.thumbnail);
	},
});
