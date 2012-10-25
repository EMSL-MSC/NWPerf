<?php
	require_once("../dbconnect.php");
	require_once("DB.php");
	$db =& DB::connect($dsn);
	$db->setFetchMode(DB_FETCHMODE_ASSOC);
	if(PEAR::isError($db)) {
		die($db->getMessage());
	}
	$res = $db->query("select nwperf_group from usergroups where nwperf_user = ? and nwperf_group = 'admin'", $_SERVER["PHP_AUTH_USER"]);
	$isAdmin = $res->numRows();
	if(array_key_exists("q", $_GET)) {
		$query = json_decode($_GET["q"],true);
		if(! $isAdmin) {
			array_push($query, array("User", $_SERVER["PHP_AUTH_USER"]));
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
		$fields = array("Start Date" => "start_time", "End Date" => "end_time", "Submit Date" => "submit_time", "Dispatch Date" => "dispatch_time", "Node Count" => "num_nodes_allocated", "User" => "moab_job_details.user", "Job Id" => "jobs.job_id", "Account" => "account");
		$sql = "select jobs.job_id as id, moab_job_details.user as user, jobs_id as jobId, account, num_nodes_allocated as numNodes, submit_time as submitTime, start_time as startTime, end_time as endTime, end_time-start_time as runTime from jobs, moab_job_details where jobs.id = moab_job_details.jobs_id and ";
		for($i=0;$i<count($query);$i++) {
			if($i != 0) {
				$sql .= "and ";
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
				case "Job Id":
				case "Account":
				case "User":
					$queryItem[0] = $fields[$queryItem[0]];
					$queryItem[1] = $db->escapeSimple($queryItem[1]);
					$sql .= "$queryItem[0] = '$queryItem[1]'";
					break;
			}
		}
		$ret = $db->getAll($sql);
		if(PEAR::isError($ret)) {
			die($ret->getMessage() . " sql: $sql for queryItems: ". var_export($query));
		}
		print(json_encode($ret));
	} else {
		$jobs_id = $_GET["job"];
		$pointsArchive = "/var/www/nwperf-graphs/flot-graphs/".($jobs_id%100)."/".($jobs_id/100%100)."/$jobs_id.tar.bz2";
		if(! file_exists($pointsArchive)) {
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
			print(json_encode(array("version" => 1, "graphs" => $ret)));
		} else {
			$query = $db->prepare("select point_description as description, name as group, pd.units as units from point_descriptions pd, point_groups pg where pd.point_groups_id = pg.id and point_name = ?");
			$ret = array();
			$pointsDir = sys_get_temp_dir()."/flot";
			if(!file_exists($pointsDir)) {
				mkdir($pointsDir);
			}
			$pointsDir .= "/$jobs_id";
			if(! file_exists($pointsDir)) {
				$phar = new PharData($pointsArchive);
				$phar->extractTo($pointsDir);
			}
			$metadata = json_decode(file_get_contents($pointsDir."/metadata"));
			foreach($metadata->points as $point) {
				$res = $db->execute($query, $point);
				$row = $res->fetchRow();
				if(! array_key_exists($row["group"], $ret)) {
					$ret[$row["group"]] = array();
				}
				array_push($ret[$row["group"]], array(	"name" => $point,
									"src" => "graphs/$jobs_id/$point",
									"unit" => $row["units"],
									"description" => $row["description"]));
			}
			print(json_encode(array("version" => 2, "graphs" => $ret, "hosts" => $metadata->hosts)));
		}
	}
?>
