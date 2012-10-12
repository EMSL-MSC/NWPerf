<?php
	require_once("../dbconnect.php");
	require_once("DB.php");
	$db =& DB::connect($dsn);
	$db->setFetchMode(DB_FETCHMODE_ASSOC);
	if(PEAR::isError($db)) {
		die($db->getMessage());
	}
	$res = $db->query("select * from usergroups where nwperf_user = ? and nwperf_group = 'admin'", $_SERVER['PHP_AUTH_USER']);
	if(PEAR::isError($res)) {
		die($res->getMessage());
	}
	if($res->numRows() > 0) {
		$res = $db->query("select distinct m.user as user from moab_job_details as m");
		if(PEAR::isError($res)) {
			die($res->getMessage());
		}
		$ret = array();
		while($row = $res->fetchRow()) {
			array_push($ret, $row["user"]);
		}
		print(json_encode($ret));
	} else {
		print(json_encode(array($_SERVER['PHP_AUTH_USER'])));
	}
?>
