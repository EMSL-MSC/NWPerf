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
	$fields = array("Start Date" => "start_time", "End Date" => "end_time", "Submit Date" => "submit_time", "Dispatch Date" => "dispatch_time");
	$sql = "select id, jobs_id, account, num_nodes_allocated, submit_time, start_time, end_time-start_time as run_time from moab_job_details where ";
	$query = json_decode($_GET["q"],true);
	for($i=0;$i<count($query);$i++) {
		if($i != 0) {
			$sql += "and ";
		}
		$queryItem = $query[$i];
		switch($queryItem[0]) {
			case "Start Date":
			case "End Date":
			case "Submit Date":
			case "Dispatch Date":
				$queryItem[0] = $fields[$queryItem[0]];
				if(! in_array($queryItem[1], array("<", ">"))) {
					next;
				}
				for($j=2;$j<count($queryItem);$j++) {
					$queryItem[$j] = $db->escapeSimple($queryItem[$j]);
				}
				$sql .= "start_time ".$queryItem[1]." '".$queryItem[4]."-".$months[$queryItem[2]]."-".$queryItem[3]." 00:00:00' ";
				break;
		}
	}
	$res = $db->getAll($sql);
	if(PEAR::isError($res)) {
		die($res->getMessage());
	}
	print(json_encode($res));
?>
