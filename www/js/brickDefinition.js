function updateSnapshot() {
	num = document.getElementById('snapshotSpace').value;
	document.getElementById('snapshotValue').innerHTML = num.toString();
}

function buildBricks() {
	// gather th values from the promppts and form some xml to 
	// govern the brick format process
	
	document.getElementById('buildBricks').disabled=true;	// turn the button off
	
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
	xml_http_post('../www/main.html', callerString, bricksDefined);

}

function bricksDefined(req) {
	
	/* req is an xml string defining the bricks just created in the format
	
	 	<data>
			<summary success='6' failed='0' />"
				<brick fsname='/gluster/brick' size='10' servername='rhs1-1' />
				<brick fsname='/gluster/brick2' size='10' servername='rhs1-1' />				  
		</data>
	*/
	
	showBusy(); // Turn off the showbusy spinner
	
	slide('bricks','volCreate'); // slide the volcreate page into view
	
	xmlString = req.responseText;
	
	xmlDoc = loadXML(xmlString);
	
	var brick = xmlDoc.getElementsByTagName("brick");
	var brickPool = document.getElementById("brickPool");
	
	for (var i=0 ; i< brick.length; i++ ) {
		var svr = brick[i].getAttribute("servername");
		var gb  = brick[i].getAttribute("size");
		var fsname = brick[i].getAttribute("fsname");
		
		var thisBrick = new Brick(svr,fsname,gb);
		var key = svr + ":" + fsname;
		
		brickList[key] = thisBrick;
		
	}
		
	populateBrickPool();
}
