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
		settingListReq = new enyo.Ajax({url: this.url})
		.response(this, function(inSender, inResponse) {
			if(parseInt(inResponse.tag) == this.settingListTag) {
				this.doNewSettingList(inResponse.settings);
			}
		})
		.go({tag: ++this.settingListTag});
		return settingListReq;
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
