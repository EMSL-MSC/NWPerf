/*
 * Copyright 2013 Battelle Memorial Institute.
 * This software is licensed under the Battelle “BSD-style” open source license;
 * the full text of that license is available in the COPYING file in the root of the repository
 */
enyo.kind({
        name: "SettingManager",
	kind: "Component",
	url: "settings/",
	events: {
		onNewSettingList: "",
		onNewSetting: ""
	},
	settingListTag: 0,
	getSettingList: function() {
		return new enyo.Ajax({url: this.url})
		.response(this, function(inSender, inResponse) {
			if(parseInt(inResponse.tag) == this.settingListTag) {
				this.doNewSettingList(inResponse.settings);
			}
		})
		.go({tag: ++this.settingListTag});
	},
	getSettingTag: 0,
	getSetting: function(settingName) {
		return new enyo.Ajax({url: this.url+settingName})
		.response(this, function(inSender, inResponse) {
			if(parseInt(inResponse.tag) == this.getSettingTag) {
				delete inResponse.tag
				this.doNewSetting(inResponse);
			}
		})
		.go({tag: ++this.getSettingTag});
		
	},
	updateSetting: function(setting, value) {
		return new enyo.Ajax({url: this.url+setting, method: "PUT"}).go({"value": value});
	},
	deleteSetting: function(name) {
		return new enyo.Ajax({url: this.url+name, method: "DELETE"}).go();
	}
});
