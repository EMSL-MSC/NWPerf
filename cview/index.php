<?php
	require_once("../dbconnect.php");
	require_once("DB.php");
	$jobs_id = $_GET["job"];
	$db =& DB::connect($dsn);
	$db->setFetchMode(DB_FETCHMODE_ASSOC);
	if(PEAR::isError($db)) {
		die($db->getMessage());
	}
	$res = $db->query("select nwperf_group from usergroups where nwperf_user = ? and nwperf_group = 'admin'", $_SERVER["PHP_AUTH_USER"]);
	if(PEAR::isError($res)) {
		die($res->getMessage());
	}
	$isAdmin = $res->numRows();

	$res = $db->query("select * from moab_job_details where moab_job_details.user = ? and jobs_id = ?", array($_SERVER["PHP_AUTH_USER"], $jobs_id));
	if(PEAR::isError($res)) {
		die($res->getMessage());
	}
	$jobOwner = $res->numRows();

	$cviewAvail = file_exists("/var/www/nwperf-graphs/cview/jobs/".($jobs_id%100)."/".($jobs_id/100%100)."/$jobs_id.tar.gz");

	if(($jobOwner || $isAdmin) && $cviewAvail) {
		header('Content-type: application/x-cviewall');
		header('Content-Disposition: attachment; filename="'.$jobs_id.'.cviewall"');
		print '{\n';
		print 'url = "http://nwperf.emsl.pnl.gov/jobs/'.$jobs_id.'/";\n';
		print 'metrics = ("cputotals.user", "meminfo.used");\n';
		print 'dataUpdateInterval = 0.0;\n';
		print '}';
	}
?>
