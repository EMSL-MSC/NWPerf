<?php
	$jobs_id = $_GET["job"];
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
?>
