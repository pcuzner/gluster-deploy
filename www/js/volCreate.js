/* ************************************************************* */
/* volCreate.js Handles the logic involved in defining a volume  */
/* ************************************************************* */

function delBrickRow(element) {
	
	var thisRow = element.parentNode.parentNode;
	var numRows = thisRow.parentNode.rows.length; // move up to tbody section, where rows property available
	
	var rowNum = thisRow.rowIndex;
	var brickDetails = thisRow.cells[0].innerHTML;

	// return the bricks to the pool
	if ( brickDetails.length > 1 ) {

		var brickNames = brickDetails.split(" ");
		for (var i = 0; i< brickNames.length; i++) {
			thisBrick = brickNames[i].replace(",","");
			brickList[thisBrick].selected = false;
			RAWGB = RAWGB - brickList[thisBrick].sizeGB
			BRICKSUSED--;
			updateSummary('stats');
		}
		thisRow.cells[0].innerHTML = " ";
		populateBrickPool();
		if ( numRows > 1) {
			thisRow.parentNode.removeChild(thisRow);
		}
	}
	
}

function updateSummary(type) {
	var usableGB = 0;
	rowCells=document.getElementById("configSummary").rows[1].cells;		
	switch(type) {
		case "volume":
			rowCells[0].innerHTML=document.getElementById("volNameInput").value;
			break;
		case "stats":
			rowCells[1].innerHTML = BRICKSUSED;
			rowCells[2].innerHTML = RAWGB;
			volType = document.getElementById("volType").value;
			
			var usableGB = ( volType == "Replicated") ? RAWGB / MAXREPLICA : RAWGB ; 

			rowCells[3].innerHTML = usableGB;
			
			break;
		case "volType":
			var volType = document.getElementById("volType").value;
			
			faultTolerance = (volType == "Replicated") ? "Single Node" : "None";
			rowCells[4].innerHTML = faultTolerance;
			break;
	}
	

}

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

function useBrick() {
	
	// check if number of bricks selected is appropriate for volume
	// type, if not drop what has been selected
	
	var numSelected = countSelected("brickPool");
	
	var volType = document.getElementById("volType").value;
	
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
						
						BRICKSUSED++;
						RAWGB = RAWGB + brickList[brickName].sizeGB;
						updateSummary('stats');
						
						// update the corresponding brick object
						
					}
				}
				
				// Remove the bricks selected from the "pool"
				removeSelected("brickPool");

			}
			
			break;
			
		case "Replicated":
			
			if ( numSelected == MAXREPLICA ) {
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
						brickString = brickString + brickName + ", ";
					}
				}

				// The number of keys = number of unique servers in the array
				if ( Object.keys(servers).length == MAXREPLICA ) {
					// remove the last separator
					brickString = brickString.slice(0,-2);
				
					var ptr = (brickTable.tBodies[0].rows.length) - 1;
					brickTable.rows[ptr].cells[0].innerHTML = brickString;
					
					addBrickRow("brickTable",2);
					removeSelected("brickPool");
					for (var i = 0; i< brickNames.length; i++) {
						brickList[brickNames[i]].selected=true;
						RAWGB = RAWGB + brickList[brickName].sizeGB;
					}
					BRICKSUSED +=2;
					updateSummary('stats');
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
		brickList[idx].selected = false;
	}
	BRICKSUSED = 0;
	RAWGB = 0;
	USABLEGB=0;
	updateSummary('stats');
	
	populateBrickPool();
}

	
function addOptions(optionName) {
	
	// Each option needs to flip the alternate option if already set
	
	switch (optionName) {
		case "Replicated":
			toggleElement("replicaCountInput");
			document.getElementById("replicaCount").setAttribute("style","position:relative;  left:85px;height:20px;opacity:100;transition:opacity .75s;");				
			// maxSelect = 2;
			document.getElementById("brickPool").selectedIndex = -1;
			
			// empty the table, and repopulate the brick pool 
			resetBricks();
			
			updateSummary("volType");

			break;
		case "Distributed":
			document.getElementById("replicaCount").setAttribute("style","position:relative;  left:85px;height:20px;opacity:0; transition:opacity .75s;");
			toggleElement("replicaCountInput");
			//maxSelect=999;
			document.getElementById("brickPool").selectedIndex = -1;				
			
			// empty the table, and repopulate the brick pool 
			resetBricks();
			
			updateSummary("volType");				

			break;
		case "Virtualisation":
			document.getElementById("virtInput").setAttribute("style","position:relative;  left:40px;height:20px;opacity:100;transition:opacity .75s;");
			toggleElement("virtUser");
			break;
		case "Streaming":
		case "Generic":
			document.getElementById("virtInput").setAttribute("style","position:relative;  left:40px;height:20px;opacity:0;transition:opacity .75s;");
			toggleElement("virtUser");
	}
}

function createVolHandler(req) {
	
	resp = req.responseText;
	
	showBusy();

	if ( resp == 'success') {
		// activate finish div	
		slide('volCreate','finish');
	}
	else {
		//activate the error page
		slide('volCreate','error');
		shutDown();
	}
}

function createVolume() {
	
	var volName = document.getElementById('volNameInput').value;
	
	if (( volName.length == 0 ) || ( BRICKSUSED == 0 )) {
		return;
	}
	
	// At this point the volume name is given, and the user has selected 
	// bricks to use, so build the xml string to pass back to the webserver
	// eg.
	// <data>
	//   <volume name='myvol' type='replicated' replica='2' usecase='virtualisation'>
	//     <protocols cifs='no' nfs='no' />
	//     <tuning target='glance' />
	//     <bricklist>
	//       <brick fullpath='server:/rhs/brick1' />
	//     </bricklist>
	//   </volume>
	// </data>
	
	var volType = document.getElementById('volType').value;
	var useCase = document.getElementById('volUseCase').value;
	var replica = ( volType == "Replicated") ? document.getElementById('replicaCountInput').value : 'none'
	var nfs     = document.getElementById('nfsRequired').checked;
	var cifs	= document.getElementById('cifsRequired').checked;
	
	var xmlString = "<data>"
					+ "<volume name='" + volName + "' type='" + volType + "' usecase='" + useCase + "'"
					+ " replica='" + replica + "' >"
					+ "<protocols nfs='" + nfs.toString() + "' cifs='" + cifs.toString() + "' />";
					
	if ( useCase == 'Virtualisation') {
		var target = document.getElementById('virtUser').value;
		xmlString += "<tuning target='" + target + "' />";
	}
	
	xmlString += "<bricklist>";
	
	// Loop through the table rows, extracting the bricks in this sequence to ensure 
	// the intended replication relationships are honoured
	var brickTable = document.getElementById('brickTable');
	var numRows = (thisTable.tBodies[0].rows.length) - 1;	// there's always an empty row at the end!

	for ( var i = 0; i<numRows; i++) {
		var cellContents = brickTable.rows[i].cells[0].innerHTML;
		var bricks = cellContents.split(", ");
		for (var ptr = 0, numBricks = bricks.length; ptr < numBricks; ptr++) {
			xmlString += "<brick fullpath='" + bricks[ptr] + "' />";
		}
		
	}
	
	xmlString += "</bricklist></volume></data>";
	
	showBusy("Creating '" + volName + "'");
	disableDiv('brickLayout');				// Need to disable separately, since it's a div within a div
	document.getElementById('volCreateBtn').disabled = true;
	
	callerString = "volCreate|" + xmlString;
	xml_http_post('../www/main.html', callerString, createVolHandler);
	
}
