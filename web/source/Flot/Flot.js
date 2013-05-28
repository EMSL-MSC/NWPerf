/*
 * Copyright 2013 Battelle Memorial Institute.
 * This software is licensed under the Battelle “BSD-style” open source license;
 * the full text of that license is available in the COPYING file in the root of the repository
 */
enyo.kind({
	name:"Flot",
	kind:"Control",
	published:{
       		src: null,
       		legend: null
	},
	events: {
		onValuesUpdate: ""
	},
	components: [
		{kind: "onyx.Popup", name: "graphSpinner", components: [
			{kind: "onyx.Spinner"}
		]}
	],
	graphData: null,
	hasPlotted: false,
	legendChanged: function(oldValue) {
		if(this.hasPlotted) {
			this.plot()
		}
	},
	updateValuesTimeout: null,
	latestPosition: null,
	previousPoint: null,
	plotItem: null,
 	scheduleUpdateValues: function (event, pos, item) {
		owner = event.data.owner;
		owner.latestPosition = pos;

		if (item) {
			if(this.previousPoint != item.dataIndex) {
				previousPoint = item.dataIndex;
				$("#tooltip").remove();
				y = item.datapoint[1].toPrecision(4);
				owner.showTooltip(item.pageX, item.pageY, item.series.label + ": " + y);
			}
		} else {
			$("#tooltip").remove();
			this.previousPoint = null
		}
		if (!owner.updateValuesTimeout) {
			owner.updateValuesTimeout = setTimeout(function(){

				owner.updateValuesTimeout = null;

				var pos = owner.latestPosition;

				var axes = owner.plotItem.getAxes();
				if (	pos.x < axes.xaxis.min && pos.x > axes.xaxis.max &&
					pos.y < axes.yaxis.min && pos.y > axes.yaxis.max)
					return;

				var i, j, dataset = owner.plotItem.getData();
				values = {};
				for (i = 0; i < dataset.length; ++i) {
					var series = dataset[i];

					// find the nearest points, x-wise
					for (j = 0; j < series.data.length; ++j)
						if (series.data[j][0] > pos.x)
							break;
					// now interpolate
					var y, p1 = series.data[j - 1], p2 = series.data[j];
					if (p1 == null)
						y = p2[1];
					else if (p2 == null)
						y = p1[1];
					else
						y = p1[1] + (p2[1] - p1[1]) * (pos.x - p1[0]) / (p2[0] - p1[0]);
					values[series.label] = y;
				}
				owner.doValuesUpdate(values);
			}, 50);
		}
	},
	plot: function() {
		var n = this.hasNode();
		if(n) {
			this.$.graphSpinner.show();
			if(this.graphData) {
				this.hasPlotted = true;
				data = []
				for(host in this.graphData) {
					points = [];
					color = "#000000";
					for(entry in this.legend) {
						entry = this.legend[entry];
						if(entry.host == host && entry.enabled) {
							color = "hsl("+entry.color[0]+", "+(entry.color[1]*100)+"%, "+(entry.color[2]*100)+"%)";
							data.push({lines: { show: true }, color: color, label: host, data: this.graphData[host]});
							break;
						}
					}
				}
				this.plotItem = $.plot(jQuery(n), data, {
					grid: {
						hoverable: true
					},
					crosshair: { mode: "x"},
					legend: {
						show: false
					},
					"yaxis": {
						tickFormatter: this.siTicks
					},
					"xaxis": {
						mode: "time",
						timezone: "browser"
					}
				});
				jQuery(n).bind("plothover",{owner: this}, this.scheduleUpdateValues);
				this.$.graphSpinner.hide();
			} else {
				new enyo.Ajax({url: this.src})
				.response(this, function(inSender, inResponse) {
					this.graphData = inResponse;
					this.plot();
				})
				.go();
			}
		}
	},
	siTicks: function(val, axis) {
		units = ["", "K", "M", "G", "T", "P"];
		for(unit in units) {
			if(val < 1000) {
				factor = Math.pow(10, axis.tickDecimals);
				return Math.round(val * factor) / factor + units[unit];
			} else {
				val /= 1000.0;
			}
		}
	},
	showTooltip: function(x, y, contents) {
		$('<div id="tooltip">' + contents + '</div>').css( {
			position: 'absolute',
			display: 'none',
			top: y - 20,
			left: x + 5,
			border: '1px solid #fdd',
			padding: '2px',
			'background-color': '#fee',
			opacity: 0.80
		}).appendTo("body").fadeIn(200);
	}
});
