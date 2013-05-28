/*
 * Copyright 2013 Battelle Memorial Institute.
 * This software is licensed under the Battelle “BSD-style” open source license;
 * the full text of that license is available in the COPYING file in the root of the repository
 */
enyo.kind({
        name: "UserManager",
	kind: "Component",
	events: {
		onGroupMembership: "",
		onUserListRetrieved: ""
	},
	getGroupMembership: function(user) {
		if(user == undefined) {
			user = "";
		}
		return new enyo.Ajax({url: "groupMembership/"+user})
		.response(this, function(inSender, inResponse) {
			this.doGroupMembership(inResponse);
		})
		.go();
	},
	getUserList: function() {
		return new enyo.Ajax({url: "users/"})
		.response(this, function(inSender, inResponse) {
			this.doUserList(inResponse);
		})
		.go();
	}
});
