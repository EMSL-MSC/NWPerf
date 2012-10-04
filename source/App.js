enyo.kind({
	name: "App",
	fit: true,
	kind: "FittableRows",
	components:[
		{kind: "QueryBuilder", style: "height: 30%"},
		{kind: "Panels", components: [
			{kind: "JobTable"},
			{kind: "JobView"},
		]},
	],
});
