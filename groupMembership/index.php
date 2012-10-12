<?php
	require_once("../dbconnect.php");
	require_once("DB.php");
	if($_GET["user"] == "") {
		$_GET["user"] = $_SERVER['PHP_AUTH_USER'];
	}
	$db =& DB::connect($dsn);
	$db->setFetchMode(DB_FETCHMODE_ASSOC);
	if(PEAR::isError($db)) {
		die($db->getMessage());
	}
	$ret = array();
	$res = $db->query("select nwperf_group from usergroups where nwperf_user = ?", $_GET["user"]);
	while($row = $res->fetchRow()) {
		array_push($ret, $row["nwperf_group"]);
	}
	print(json_encode($ret));
	//print(json_encode(array()));
?>
