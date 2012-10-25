<?php
	$jobs_id = $_GET["job"];
	$pointArchiveDir = sys_get_temp_dir()."/flot/$jobs_id";
	if(file_exists($pointsArchiveDir)) {
		$pointsDir = "/var/www/nwperf-graphs/".($jobs_id%100)."/".($jobs_id/100%100)."/".$jobs_id;
		$pointsDescFile = $pointsDir."/pointsDescriptions";
		$file = fopen($pointsDescFile,'r');
		$fstat = fstat($file);
		$jobData = unserialize(fread($file, $fstat["size"]));
		$res = array();
		
		foreach($jobData as $graph) {
			if($graph["name"] == $_GET["metric"]) {
				$pointGraph = $pointsDir."/job.".$_GET["job"]."-point.".$graph["point_id"].".png";
				break;
			}
		}
		if(file_exists($pointGraph)) {
			header("content-Type: image/png");
			readfile($pointGraph);
		}
	} else {
		$f = file_get_contents($pointArchiveDir."/".$_GET["metric"].".flot", "r");
		if($f) {
			$graph = json_decode($f);
			$ret = array(	"endTime" => $graph->endTime*1000,
					"startTime" => $graph->startTime*1000,
					"data" => array());
			if(isset($graph->downSampledData)) {
				$ret["data"] = $graph->downSampledData;
			} else {
				foreach($graph->data as $host => $points) {
					if(! array_key_exists($host, $ret["data"])) {
						$ret["data"][$host] = array();
					}
					for($i=0;$i<count($points);$i++) {
						$point = array($i*60000+$ret["startTime"], $points[$i]);
						$ret["data"][$host][$i] =  $point;
					}
				}
			}
			print(json_encode($ret));
		}
	}
?>
