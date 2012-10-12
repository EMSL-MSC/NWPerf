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
		this.$.jobGraphs.createComponent({kind: "onyx.Spinner"});
		this.$.jobGraphs.render();
	},
	jobChanged: function(oldValue) {
		this.$.jobGraphs.destroyClientControls();
		this.$.jobGraphs.render();
		length = 0;
		for(group in this.job) {
			if(group == "originator") {
				continue;
			}
			length++;
			groupHeader = this.$.jobGraphs.createComponent({content: group, ontap: "toggleDrawer", classes: "group-header"}, {owner:  this});
			groupDrawer = this.$.jobGraphs.createComponent({kind: "onyx.Drawer", open: false});
			groupHeader.drawer = groupDrawer;
			for(metric in this.job[group]) {
				headerText = this.job[group][metric]["name"]+" - "+ this.job[group][metric]["description"];
				metricHeader = groupDrawer.createComponent({content: headerText, ontap: "toggleDrawer", classes: "image-header"}, {owner:  this})
				metricDrawer = groupDrawer.createComponent({kind: "onyx.Drawer", open: false});
				metricHeader.drawer = metricDrawer;
				metricDrawer.createComponent({kind: "Image", src: this.job[group][metric]["src"], ontap: "toggleThumbnail", classes: "thumbnail", thumbnail: true}, {owner: this});
			}
		}
		if(length == 0) {
			this.$.jobGraphs.createComponent({content: "Sorry there is no data for this job", classes:"job-error"});
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
