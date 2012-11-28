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
		groupMembership = new enyo.Ajax({url: "groupMembership/"+user})
		.response(this, function(inSender, inResponse) {
			this.doGroupMembership(inResponse);
		})
		.go();
		return groupMembership;
	},
	getUserList: function() {
		userList = new enyo.Ajax({url: "users/"})
		.response(this, function(inSender, inResponse) {
			this.doUserList(inResponse);
		})
		.go();
		return userList;
	}
});
