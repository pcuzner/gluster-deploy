//
// disk discovery and selection logic
//

function startDiskDiscovery() {

	showBusy(); // turn of the busy dialog
	slide("disks");
	
	
}

function showDisks(req) {
	
	showBusy();


	
	document.getElementById('diskArea').className = 'show';

	var xmlDoc = req.responseXML;
	
	// populate the table with the data received
	var diskTable = document.getElementById('diskTable').getElementsByTagName('tbody')[0];
	var nodes = xmlDoc.getElementsByTagName('node');	// nodes is an array
	var numNodes = nodes.length;						// how many nodes have I got?
	
	for (var n = 0 ; n< numNodes; n++) {
		
		var nodeName = nodes[n].getElementsByTagName('nodename')[0].getAttribute('name');
		var devices = nodes[n].getElementsByTagName('disks')[0].childNodes;
		var numDevs = devices.length;
		
		for (var i = 0; i< numDevs; i++) {
			devID=devices[i].getAttribute('id');
			devSize=devices[i].getAttribute('size');
			
			var newRow = diskTable.insertRow(-1);		// insert to the end of the table
			
			var col1 = newRow.insertCell(0); 	// Insert the column for Server Name
			

			var col2 = newRow.insertCell(-1); // device ID
			var col3 = newRow.insertCell(-1); // Size (GB)
			var col4 = newRow.insertCell(-1); // checkbox
			
			col1.innerHTML=nodeName;
			col2.innerHTML=devID;
			col3.innerHTML=devSize;
			checkBox = "<input type='checkbox' name='selectDisk' id='" +nodeName + "_" + devID + "' onchange='resetSelectAll()'/>"
			col4.innerHTML=checkBox;
		}
	}
	document.getElementById('registerBricks').className = 'registerButton';
	
}

function selectAll() {
	// Called when the user clicks the check box in the column heading
	// to trigger all the row checkboxes to be selected/unselected
	if (document.getElementById('allDisks').checked == true) {
		updateCheckbox('selectDisk',true)
	}
	else {
		updateCheckbox('selectDisk',false)
	}
	
}

function resetSelectAll() {
	// turn of the check state of the selectAll element
	document.getElementById('allDisks').checked = false;
	
}


function findDisks() {

	document.getElementById('getDisks').disabled = true;
		
	showBusy('Scanning nodes for unused disks');
	
	var xmlString = "<data><request-type>find-disks</request-type></data>";
	
	xml_http_post('../www/main.html', xmlString, showDisks);
	
	
}

function registerHandler(req) {

	xmlDoc = req.responseXML;
	
	// Example XML input
	// <response>
	//   <status-text>OK</status-text>
	//   <brick path='/gluster/brick1' vgname='bla' lvname='wah' />
	//   <features snapshot='YES' btrfs='NO' />
	// </response>
	
	var state = xmlDoc.getElementsByTagName("status-text")[0].childNodes[0].nodeValue;
	
	if (state == 'OK') {
		// trigger slide transition to build bricks page
		// slide('bricks');
		var features = xmlDoc.getElementsByTagName('features')[0].attributes;
		var snapshotEnabled = features.getNamedItem('snapshot').value;
		var btrfsEnabled = features.getNamedItem('btrfs').value;
		
		var brickInfo = xmlDoc.getElementsByTagName('brick')[0].attributes;
		var brickPath = brickInfo.getNamedItem('path').value;
		var brickVG   = brickInfo.getNamedItem('vgname').value;
		var brickLV   = brickInfo.getNamedItem('lvname').value;
		
		
		document.getElementById('mountPoint').value = brickPath;
		document.getElementById('vgName').value = brickVG;
		document.getElementById('lvName').value = brickLV;
		
		if (btrfsEnabled == 'YES' ) {
			// Add btrfs to the select options
			var target = document.getElementById('brickProvider');
			var newOption = document.createElement('option');
			newOption.text = "BTRFS";
			target.add(newOption, null);	// FF, Chrome, Opera IE8+
			
		}
		

		if (snapshotEnabled == 'YES') {
			// change the class of the 
			document.getElementById('snapRequired').className = 'show';
			
		}
	
		slide('bricks');
    
	}
	


	
}	

function registerBricks() {
	// check if any of the checkboxes are selected
	var checkboxes = document.getElementsByName('selectDisk');
	var numCheckboxes = checkboxes.length;
	var workToDo = false;
	for (var n = 0; n< numCheckboxes; n++) {
		if (checkboxes[n].checked) {
			workToDo = true;
			break;
		}
		
	}
	
	if (workToDo) {
	// loop through each check box
		var xmlString = '<data><request-type>register-bricks</request-type>';
		var numBricks = 0;
		
		for (var n = 0; n<numCheckboxes; n++ ) {
			
			if (checkboxes[n].checked) {
				numBricks++;
				var idName = checkboxes[n].id;
				var part = idName.split('_');
				var nodeName = part[0];
				var devID = part[1];
				
				xmlString += "<device host='" + nodeName + "' device='" + devID + "' />"
			}
		}
		xmlString += '</data>';
		//callerString = 'registerBricks|' + callerParms;
		// showBusy('Creating 	' + numBricks + ' bricks');
		
		xml_http_post('../www/main.html', xmlString, registerHandler);
	
	}
	
	
	// if not, do nothing
	

	
}
