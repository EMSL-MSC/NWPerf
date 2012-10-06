<?php
	require_once("../dbconnect.php");
	require_once("DB.php");
	$db =& DB::connect($dsn);
	if(PEAR::isError($db)) {
		die($db->getMessage());
	}
	$months = array("Jan" => 1,
			"Feb" => 2,
			"Mar" => 3,
			"Apr" => 4,
			"May" => 5,
			"Jun" => 6,
			"Jul" => 7,
			"Aug" => 8,
			"Sep" => 9,
			"Oct" => 10,
			"Nov" => 11,
			"Dec" => 12);
	$sql = "select id, jobs_id, account, num_nodes_allocated, submit_time, start_time from moab_job_details where ";
	$query = json_decode($_GET["q"],true);
	print_r($_GET["q"]);
	print_r($query);
/*
	for($i=0;$i<count($query);$i++) {
		if($i != 0) {
			$sql += "and ";
		}
		$queryItem = $_GET["q"][$i];
		switch($queryItem[0]) {
			case "Start Date":
				if(! in_array($queryItem[1], array("<", ">"))) {
					next;
				}
				for($j=2;$j<count($queryItems);$j++) {
					$queryItems[$j] = $db->escapeSimple($queryItems[$j]);
				}
				$sql += "start_time "+$queryItem[1]+" '"$queryItems[4]+"-"+$months[$queryItems[2]]+"-"+$queryItems[3]+" 00:00:00' ";
				break;
		}
	}
	print $sql;
*/
?>
