<?php
	require_once("../dbconnect.php");
	require_once("DB.php");
	$db =& DB::connect($dsn);
	$db->setFetchMode(DB_FETCHMODE_ASSOC);
	if(PEAR::isError($db)) {
		die($db->getMessage());
	}
	if(array_key_exists("q", $_GET)) {
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
		$fields = array("Start Date" => "start_time", "End Date" => "end_time", "Submit Date" => "submit_time", "Dispatch Date" => "dispatch_time", "Node Count" => "num_nodes_allocated");
		$sql = "select id, jobs_id as jobId, account, num_nodes_allocated as numNodes, submit_time as submitTime, start_time as startTime, end_time as endTime, end_time-start_time as runTime from moab_job_details where ";
		$query = json_decode($_GET["q"],true);
		$userSpecified = false;
		for($i=0;$i<count($query);$i++) {
			if($i != 0) {
				$sql .= "and ";
			}
			$queryItem = $query[$i];
			if($queryItem[0] == "User Name") {
				$userSpecified = true;
			}
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
					$sql .= "$queryItem[0] $queryItem[1] '$queryItem[4]-".$months[$queryItem[2]]."-$queryItem[3] 00:00:00' ";
					break;
				case "Node Count":
					$queryItem[0] = $fields[$queryItem[0]];
					if(! in_array($queryItem[1], array("<", ">", "==", "<=", ">="))) {
						next;
					}
					for($j=2;$j<count($queryItem);$j++) {
						$queryItem[$j] = $db->escapeSimple($queryItem[$j]);
					}
					$sql .= "$queryItem[0] $queryItem[1] '$queryItem[2]' ";
					break;
					
			}
		}
		if(! $userSpecified) {
			if(count($query) > 0) {
				$sql .= "and ";
			}
			#$sql .= "user = '".$db->escapeSimple($_SERVER['PHP_AUTH_USER'])."' ";
			$sql .= "moab_job_details.user = 'dbaxter' ";
		}
		$ret = $db->getAll($sql);
		if(PEAR::isError($ret)) {
			die($ret->getMessage() . " sql: $sql for queryItems: ". var_export($query));
		}
		print(json_encode($ret));
	} else {
		$jobs_id = $_GET["job"];
		$query = $db->prepare("select point_description from point_descriptions where id = ?");
		$pointsDir = "/var/www/nwperf-graphs/".($jobs_id%100)."/".($jobs_id/100%100)."/".$jobs_id;
		$pointsDescFile = $pointsDir."/pointsDescriptions";
		$file = fopen($pointsDescFile,'r');
		$fstat = fstat($file);
		$jobData = unserialize(fread($file, $fstat["size"]));
		$ret = array();
		foreach($jobData as $graph) {
			if(file_exists($pointsDir."/job.$jobs_id-point.".$graph["point_id"].".png")) {
				if(! array_key_exists($graph["group"], $ret)) {
					$ret[$graph["group"]] = array();
				}
				$res = $db->execute($query, $graph["point_id"]);
				$row = $res->fetchRow();
				$description = $row["point_description"];
				array_push($ret[$graph["group"]], array("name" => $graph["name"],
									"src" => "graphs/$jobs_id/".$graph["name"],
									"description" => $description));
			}
		}
		print(json_encode($ret));
	}
?>
