
/* ************************************************************* */
/* volCreate.js handles the logic involved in defining a volume  */
/* ************************************************************* */

function addBrickRow(tableName, numCells) {
	
	thisTable = document.getElementById(tableName);
	var row = thisTable.insertRow(-1); 		// add new row to the end
	for ( var i=0 ; i< numCells; i++) {
		var newcell = row.insertCell(i);	// add cells to new row
		if (i < (numCells -1)) {
			newcell.innerHTML = " ";
		}
		else { // this is last cell so add a button
			newcell.innerHTML = "<button class='btn delbtn' onclick='delBrickRow(this)'><i class='icon-cancel'></i></button>";
		}
	}
	
}

function delBrickRow(element) {
	
	var thisRow = element.parentNode.parentNode;
	var numRows = thisRow.parentNode.rows.length; // move up to tbody section, where rows property available
	
	var rowNum = thisRow.rowIndex;
	var brickDetails = thisRow.cells[0].innerHTML;

	// return the bricks to the pool
	if ( brickDetails.length > 1 ) {

		var brickNames = brickDetails.split(",");
		for (var i = 0; i< brickNames.length; i++) {
			thisBrick = brickNames[i].replace(",","");
			brickList[thisBrick].selected = false;
		}
		
		thisRow.cells[0].innerHTML = " ";
		populateBrickPool();
		if ( numRows > 1) {
			thisRow.parentNode.removeChild(thisRow);
		}
	}
	
	// ensure the input fields/buttons are all enabled
	document.getElementById('useBrick').disabled=false;
	
	inputFieldsDisabled(false);
	
	// without bricks selected, the queuevolume button can be disabled
	if ((bricksSelected() == 0) || ( bricksSelected() == bricksQueued() )) {
		document.getElementById('queueVolume').disabled=true;
		inputFieldsReset();
	}
	else {
		document.getElementById('queueVolume').disabled=false;
	}
	
	
	
}

function validHadoopPath(pathName) {
	
	var pathOK = false;
	
	if ( validPathName(pathName)) {
		
		pathOK = true;		// path itself is valid
		
		// now check for this path already being provided against another
		// volume in the 'queue'
		for (idx in glusterVolumeList) {
			
			var thisVol = glusterVolumeList[idx];
			if ( thisVol.hadoopMountPoint == pathName ) {
				pathOK = false;
				break;
			}
		}
	}
	
	return pathOK;
}


function useBrick() {
	
	
	// the volname and directory should be provided first, so check these are set
	var volName = document.getElementById('volNameInput').value;
	var dirName = document.getElementById('volDir').value;
	var useCase = document.getElementById('volUseCase').value;
	
	var validRequest = true;
	
	if ( ! volNameUsable(volName) ) {
		validRequest = false;
	}
	if (dirName.length == 0) {
		document.getElementById('volDir').className = "error";
		validRequest = false;
	}
	
	// if the user has selected the hadoop usecase, the mount point field 
	// MUST be supplied
	if ( useCase.toLowerCase() == 'hadoop') {
		var thisMountPoint = document.getElementById('hadoopMountPoint').value;
		if ( ( thisMountPoint.length == 0) || ( ! validHadoopPath(thisMountPoint)) ) {
			validRequest = false;
			document.getElementById('hadoopMountPoint').className = "error";
		}
	}
	
	if ( ! validRequest ) {
		return;
	}
	
	
	// At this point we have bricks selected and volume/dir specified
	document.getElementById('volNameInput').className = " ";
	document.getElementById('volDir').className = " ";
	document.getElementById('hadoopMountPoint').className = " ";
	
	// check if number of bricks selected is appropriate for volume
	// type, if not drop what has been selected
	
	var numSelected = countSelected("brickPool");
	
	var volType = document.getElementById("volType").value;
	
	var validSelection = false;
	
	bricks = document.getElementById("brickPool");
	brickTable = document.getElementById("brickTable");
	
	switch(volType) {
		case "Distributed":
			// get the current size of the table as ptr
			
			if ( numSelected > 0 ) {
			
				var ptr = (brickTable.tBodies[0].rows.length) - 1;
				for (var i = 0; i < bricks.options.length; i++) {
					if (bricks.options[i].selected == true) {
						var brickText = bricks.options[i].value;
						var brickName = brickText.substr(0,brickText.indexOf("("));
						brickTable.rows[ptr].cells[0].innerHTML = brickName;
						brickList[brickName].selected = true;
						ptr++;
						addBrickRow("brickTable",2);
						
						//BRICKSUSED++;
						//RAWGB = RAWGB + brickList[brickName].sizeGB;
						
						document.getElementById('queueVolume').disabled=false;						
						
						// updateSummary('stats');
						
						// update the corresponding brick object
						
					}
				}
				
				validSelection = true;
				
			}
			
			break;
			
		case "Replicated":
			var replicaCount = parseInt(document.getElementById('replicaCountInput').value);
			if ( numSelected == replicaCount ) {
				// Using an assoc array to hold the server names, then 
				// this can be 'counted' to ensure that all the servers 
				// providied are unique

				
				var servers = {}, brickNames = [], brickString = "";
				
				for (var i = 0; i < bricks.options.length; i++) {
					if (bricks.options[i].selected == true) {
						var brickText = bricks.options[i].value;
						var brickName = brickText.substr(0,brickText.indexOf("("));
						brickNames.push(brickName);	// Add brick name to the list of bricks
						var svrName = brickText.substr(0,brickText.indexOf(":"));

						servers[svrName] = "OK";
						brickString = brickString + brickName + ",";
					}
				}

				// The number of keys = number of unique servers in the array
				if ( Object.keys(servers).length == MAXREPLICA ) {
					// remove the last separator
					brickString = brickString.slice(0,-1);
				
					var ptr = (brickTable.tBodies[0].rows.length) - 1;
					brickTable.rows[ptr].cells[0].innerHTML = brickString;
					
					addBrickRow("brickTable",2);
					
					for (var i = 0; i< brickNames.length; i++) {
						brickList[brickNames[i]].selected=true;
						//RAWGB = RAWGB + brickList[brickName].sizeGB;
					}
					
					validSelection = true;
					break;
					
				}
				else { // User given bricks on same node, which is invalid 

					document.getElementById("brickPool").selectedIndex = -1; // Remove all selections in the select box
				}
				
			}			
			else { // User has not provided 2 bricks for a replica pair

				document.getElementById("brickPool").selectedIndex = -1; // Remove all selections in the select box
			}
			
			break;
	}
	
	if ( validSelection ) {
		// Remove the bricks selected from the "pool"
		removeSelected("brickPool");

		// If there are no more bricks to select, disable the 'input' fields/buttons
		if ( bricksSelected() == TOTALBRICKS ) {
			document.getElementById('useBrick').disabled=true;
			if (consoleOK && debugON) { console.info("UseBrick logic turning off useBrick button");}
		}
		else {
			document.getElementById('useBrick').disabled=false;
			if (consoleOK && debugON) { console.info("UseBrick logic turning on useBrick button");}
		}
		

		// UI enable the queuevolume button
		document.getElementById('queueVolume').disabled=false;
	}
	
	
}

function inputFieldsReset() {
	document.getElementById('volNameInput').value = '';
	document.getElementById('volDir').value = ''; 
	document.getElementById('nfsRequired').checked = false;
	document.getElementById('cifsRequired').checked = false;
	document.getElementById('hadoopMountPoint').value="";
	
	document.getElementById('volType').value="Distributed";
	document.getElementById('replicaCount').className=" ";
	document.getElementById('volUseCase').value="Generic";
	document.getElementById('virtInput').className=" ";
	document.getElementById('hadoopInput').className=" ";
	
}



function inputFieldsDisabled(state) {
	document.getElementById('volNameInput').disabled=state;
	document.getElementById('volUseCase').disabled=state;
	document.getElementById('volType').disabled=state;
	document.getElementById('volDir').disabled=state;
	document.getElementById('hadoopMountPoint').disabled=state;
	document.getElementById('replicaCountInput').disabled=state;
	
	
}

function bricksQueued() {
	var queued = 0;
	for (idx in brickList) {
		if ( brickList[idx].queued) {
			queued++;
		}
	}

	return queued;
}

function bricksSelected() {
	var selected = 0;
	
	for (idx in brickList) {
		if ( brickList[idx].selected) {
			selected++;
		}
	}

	return selected;
}

function volNameUsable(volumeName) {
	
	var volState = true;
	
	if ( volumesQueued() > 0) {
						
		if (volumeName in glusterVolumeList) {
			volState = false; 
		}
	}
	
	if (volumeName.length == 0) {
		volState = false;
	}
	
	return volState;
}



function validateVolName(volumeName) {
	// Check thif there are volumes in the queue
	
	if ( volNameUsable(volumeName) ) {
		document.getElementById('volNameInput').className = "";				
	}
	else {				
		document.getElementById('volNameInput').className = "error";
		if (consoleOK && debugON) { console.warning("Volume name provided is invalid - error passed back to user");}
			
	}
	
}


function volumesQueued() {
	return Object.keys(glusterVolumeList).length;
}



function queueVolume() {
	// take the contents of the selected brick table, and create a volume
	// object and populate the configSummary table
	
	var volName = document.getElementById('volNameInput').value;
	var volDirectory = document.getElementById('volDir').value;
	
	// first, the simple reasons to do Nothing!
	if (( volName.length == 0 ) || ( bricksSelected() == 0 ) || (volDirectory.length == 0)) {
		return;
	}
	
	var volType = document.getElementById('volType').value;
	var useCase = document.getElementById('volUseCase').value;
	var nfs     = document.getElementById('nfsRequired').checked;
	var cifs	= document.getElementById('cifsRequired').checked;
	var hadoopPath = document.getElementById('hadoopMountPoint').value;
	
	var target	= (	useCase == 'Virtualisation') ? document.getElementById('virtUser').value : 'None';			

	
	// Loop through the table rows, extracting the bricks in this sequence to ensure 
	// the intended replication relationships are honoured
	var brickTable = document.getElementById('brickTable');
	var numRows = (brickTable.tBodies[0].rows.length) - 1;	// there's always an empty row at the end!
	var brickListStr = '';
	var rawGB = 0;
	var usableGB = 0;

	for ( var i = 0; i<numRows; i++) {

		
		var cellContents = brickTable.rows[i].cells[0].innerHTML;

				
		var bricks = cellContents.split(",");
		var numBricks = bricks.length ;
		for (var ptr = 0; ptr < numBricks; ptr++) {
			var brickPath = bricks[ptr] ;
			rawGB += brickList[brickPath].sizeGB;
			brickListStr += brickPath + ',';
			
			brickList[brickPath].queued=true;
		}
		
	}
	
	if (consoleOK && debugON) { console.log("brick list created is %s",brickListStr);}
	
	// remove the bricks from the selected brick list
	emptyTable('brickTable');
	
	if (document.getElementById('volType').value == 'Replicated' ) {
		element = document.getElementById('replicaCountInput');
		var replicaCount = parseInt(element.options[element.selectedIndex].text);
		usableGB = rawGB / replicaCount;		
	}
	else {
		
		usableGB = rawGB
		var replicaCount = 1;
	}
	
	// remove trailing ',' from the concatenation operation
	brickListStr = brickListStr.substring(0,brickListStr.length - 1);
	
	var newVol = new GlusterVolume(volName, useCase, target, volDirectory, volType, nfs, cifs, brickListStr, rawGB, usableGB, replicaCount, hadoopPath) ;
	glusterVolumeList[volName] = newVol;
	
	if (consoleOK && debugON) { console.info("Creating new volume object"); console.dir(newVol);}
	
	var configSummary = document.getElementById('configSummary');
	
	// add this volumes definition to the configSummary table
	var ptr = (configSummary.tBodies[0].rows.length) - 1;
	updatedRow = newVol.rowOutput();
	
	updatedRow += "<td><button class='delbtn' onclick='delVolumeRow(this)'><i class='icon-cancel'></i></button></td>"
	configSummary.rows[ptr].innerHTML = updatedRow;
	
	addVolumeRow();
	
	// reset volume parameters
	inputFieldsReset();
		
	// enable the commit button and disable the queue button
	document.getElementById('volCreateBtn').disabled=false;
	document.getElementById('queueVolume').disabled=true;
	
	// if all the bricks are now in the queue, disable the input fields
	if (( bricksSelected() == bricksQueued() ) && (bricksSelected() == TOTALBRICKS)) {
		inputFieldsDisabled(true);
	}
	
}

function addVolumeRow() {
	//
	var configSummary = document.getElementById('configSummary');
	var row = configSummary.insertRow(-1); 		// add new row to the end
	var numCells = 6;
	for ( var i=0 ; i< numCells; i++) {
		var newcell = row.insertCell(i);	// add cells to new row
		if (i < (numCells -1)) {
			newcell.innerHTML = " ";
		}
		else { // this is last cell so add a button
			newcell.innerHTML = "<button class='btn delbtn' onclick='delVolumeRow(this)'><i class='icon-cancel'></i></button>";
		}
	}	
}

function delVolumeRow(element) {
	// remove a volume from the config summary
	// 1. return current contents of selected to the candidate box
	// 2. populate selected with volume details
	// 3. remove volume entry from table
	// 4. drop volume object
	
	// 1. 
	// return all non queued bricks to the brick pool
	resetBricks();

	// 2. 
	var thisRow = element.parentNode.parentNode;
	var volName = thisRow.cells[0].innerHTML;
	
	// reset the elements on the page to the volume settings removed
	// from the queue
	var thisVol = glusterVolumeList[volName];
	document.getElementById('volNameInput').value = thisVol.volumeName;
	document.getElementById('volDir').value = thisVol.mountPoint;
	document.getElementById('cifsRequired').checked = thisVol.cifsEnabled;
	document.getElementById('nfsRequired').checked = thisVol.nfsEnabled;
	document.getElementById('volUseCase').value = thisVol.useCase;
	
	document.getElementById('volType').value = thisVol.volumeType;
	if ( thisVol.volumeType == "Replicated" ) {
		document.getElementById('replicaCount').className="show";
		document.getElementById('replicaCountInput').value=thisVol.replicaCount;
	}
	else {
		document.getElementById('replicaCount').className=" ";
	}
	
		
	switch(thisVol.useCase) {
		case "Virtualisation":
			document.getElementById('virtUser').value=thisVol.target;
			document.getElementById('virtInput').className="show";
			document.getElementById('virtUser').disabled=false;
			document.getElementById('hadoopInput').className=" ";
			break;
		case "Hadoop":
			document.getElementById('hadoopMountPoint').value=thisVol.hadoopMountPoint;
			document.getElementById('hadoopInput').className="show";
			document.getElementById('virtInput').className=" ";
			document.getElementById('hadoopMountPoint').disabled=false;
			break;
	}
	
	inputFieldsDisabled(false);
	
	// update the use caase and volume type fields from the volume attributes
	
	var brickStr = thisVol.brickList;
	
	if (consoleOK && debugON) { console.info("Removing volume from the queue"); console.dir(thisVol);}
	
	var replicaCount = thisVol.replicaCount;
	
	// populate the brickTable with this volumes bricks
	var brickArray = brickStr.split(',');
	var iterations = brickArray.length / replicaCount;
	for (var i = 0; i < iterations; i++) {
		var brickSet = brickArray.splice(0, replicaCount); 
		
		// remove the queued flag for each of the bricks
		for (idx in brickSet){
			var pathName = brickSet[idx];
			brickList[pathName].queued=false;
		}
		
		var ptr = (brickTable.tBodies[0].rows.length) - 1;
		
		brickTable.rows[ptr].cells[0].innerHTML = brickSet;
		
		addBrickRow("brickTable",2);

	}
	
	// 3.
	var numRows = thisRow.parentNode.rows.length;
	if ( numRows > 1) {
		thisRow.parentNode.removeChild(thisRow);
	}
	else {
		var numCells = thisRow.cells.length -1;
		for (var i = 0; i<numCells; i++) {
			thisRow.cell[i].innerHTML=" ";
		}
	}

	
	
	// 4.
	delete glusterVolumeList[volName];
	if (consoleOK && debugON) { console.info("Volume queue now has %d entries",volumesQueued());}
	
	// UI - if volumesqueued == 0 turn off the commit button
	if ( volumesQueued() == 0 ) {
		document.getElementById('volCreateBtn').disabled=true;
	}
	
	// selected bricks pool now has entries again, so enable the queuevolume button
	document.getElementById('queueVolume').disabled=false;
	
}


function populateBrickPool() {
	
	brickPool = document.getElementById("brickPool");
	
	// drop all existing entries from the select box
	for (var i = brickPool.options.length-1; i >= 0; i--) {
		brickPool.remove(i);
	}

	// Populate the select box from the full brick list
	for (var idx in brickList) {
		if ( ! brickList[idx].selected ) {
			optionText  = brickList[idx].brickPath 
						+ "(" + formatGB(brickList[idx].sizeGB) 
						+ ")";
			brickList[idx].selected = false;
			brickPool[brickPool.length] = new Option(optionText);
		}
	}
}



function resetBricks() {
	
	emptyTable("brickTable");
	
	for (var idx in brickList) {
		if ( brickList[idx].queued == false) {
			brickList[idx].selected = false;
		}
	}
	
	populateBrickPool();
}

	
function addOptions(optionName) {
	
	// Each option needs to flip the alternate option if already set
	
	switch (optionName) {
		case "Replicated":
			document.getElementById("replicaCountInput").disabled=false;
			//document.getElementById("replicaCount").setAttribute("style","position:relative;  left:85px;height:20px;opacity:100;transition:opacity .75s;");				
			document.getElementById("replicaCount").className = "show";
			
			// maxSelect = 2;
			document.getElementById("brickPool").selectedIndex = -1;
			
			// empty the table, and repopulate the brick pool 
			resetBricks();
			
			break;
			
		case "Distributed":
			//document.getElementById("replicaCount").setAttribute("style","position:relative;  left:85px;height:20px;opacity:0; transition:opacity .75s;");
			document.getElementById("replicaCount").className=" ";
						document.getElementById("replicaCountInput").disabled=true;
			//toggleElement("replicaCountInput");
			
			//maxSelect=999;
			document.getElementById("brickPool").selectedIndex = -1;				
			
			// empty the table, and repopulate the brick pool 
			resetBricks();

			break;
			
		case "Virtualisation":
			//document.getElementById("virtInput").setAttribute("style","position:relative;  left:40px;height:20px;opacity:100;transition:opacity .75s;");
			document.getElementById("virtInput").className="show";
			document.getElementById('hadoopInput').className=" ";
			document.getElementById('hadoopMountPoint').disabled=true;
			document.getElementById('virtUser').disabled=false;
			//toggleElement("virtUser");
			break;

		case "Hadoop":
			document.getElementById('hadoopInput').className="show";
			document.getElementById('hadoopMountPoint').disabled=false;
			document.getElementById('virtInput').className=" ";
			document.getElementById('virtUser').disabled=true;
			//toggleElement(';
			break;
			
		case "Streaming":
		case "Generic":
			document.getElementById("virtInput").className=" ";
			document.getElementById('hadoopInput').className=" ";
			// document.getElementById("virtInput").setAttribute("style","position:relative;  left:40px;height:20px;opacity:0;transition:opacity .75s;");
			document.getElementById('hadoopMountPoint').disabled=true;
			document.getElementById('virtUser').disabled=true;
			//toggleElement("virtUser");
			
	}
}

function createVolHandler(req) {
	
	var xmlDoc = req.responseXML;
	var state = xmlDoc.getElementsByTagName("status-text")[0].childNodes[0].nodeValue;
	
	// Add next button
	// add onclick definition
	// change the spinner to a green tick
	if ( state == 'OK' ) {
		document.getElementById('busyGraphic').className = 'success';
		document.getElementById('busyButton').onclick = function() { showBusy(); getSummary();};
		
	}
	else {
		document.getElementById('busyGraphic').className = 'fail';
		document.getElementById('busyButton').onclick = function() { showError();};
	}
																										
	document.getElementById('busyButton').disabled = false;
	document.getElementById('busyButton').style.visibility = 'visible';

}


function createVolumes() {
	

	var xmlString = "<data><request-type>vol-create</request-type>";

	for (idx in glusterVolumeList) {
		xmlString += glusterVolumeList[idx].dumpXML();
	}
	
	xmlString += "</data>";
	
	var volsToCreate = volumesQueued();
	var sfx = (volsToCreate > 1) ? 's' : '';
	
	showBusy("Creating " + volsToCreate + " volume" + sfx);
	disableDiv('brickLayout');				// Need to disable separately, since it's a div within a div
	disableDiv('volCreate');
	
	xml_http_post('../www/main.html', xmlString, createVolHandler);
	
	enableMsgLog();
	
}
