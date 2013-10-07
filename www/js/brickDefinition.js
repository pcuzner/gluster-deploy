function updateSnapshot() {
	num = document.getElementById('snapshotSpace').value;
	document.getElementById('snapshotValue').innerHTML = num.toString();
}

function buildBricks() {
	// gather th values from the promppts and form some xml to 
	// govern the brick format process
	
	var useCase = document.getElementById('useCase').value;
	var snapshotReserve = document.getElementById('snapshotSpace').value;
	var volumeGroup = document.getElementById('volGroupName').value;
	var mountPoint = document.getElementById('mountPoint').value;
	
	// Create XML string
	
	retString = "<brickparms><parms usecase='" + useCase + "' ";
	retString = retString + "snapreserve='" + snapshotReserve.toString() + "' ";
	retString = retString + "volgroup='" + volumeGroup + "' ";
	retString = retString + "mountpoint='" + mountPoint + "'/></brickparms>";
	
	callerString = 'buildBricks|';
	callerString = callerString + retString;
	
	showBusy('Creating Bricks');
	
	// Pass the string back to the server
	xml_http_post('../www/main.html', callerString, finish);
	// --> handler is finish
}

function finish(req) {
	
	showBusy();
	
	slide('bricks','finish');
	slide('bricks','finish');
}
