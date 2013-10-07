
// disk management

function startDiskDiscovery() {

	showBusy(); // turn of the busy dialog
	slide("keys","disks");
	
	
}

function showDisks(req) {
	showBusy();

	document.getElementById('getDisks').disabled = true;
	
	document.getElementById('diskArea').className = 'show';
	
	// Load the data received into an DOM for easier navigation
	if (window.DOMParser) {
		parser = new DOMParser();
		xmlDoc = parser.parseFromString(req.responseText,"text/xml");
	}
	else { // for IE
		xmlDoc=new ActiveXObject("Microsoft.XMLDOM");
		xmlDoc.async=false;
		xmlDoc.loadXML(req.responseText); 
	}
	
	// populate the table with the data received
	var diskTable = document.getElementById('diskTable');
	var nodes = xmlDoc.getElementsByTagName('node');	// nodes is an array
	var numNodes = nodes.length;						// how many nodes have I got?
	
	for (var n = 0 ; n< numNodes; n++) {
		
		var nodeName = nodes[n].getElementsByTagName('nodename')[0].getAttribute('name');
		var devices = nodes[n].getElementsByTagName('disks')[0].childNodes;
		var numDevs = devices.length;
		
		for (var i = 0; i< numDevs; i++) {
			devID=devices[i].getAttribute('id');
			devSize=devices[i].getAttribute('size');
			
			var newRow = diskTable.insertRow(-1);
			var col1 = newRow.insertCell(0); // Server Name
			col1.rowSpan = numDevs;						// set number of rows for this cell based on 
														// the number of devices found on this host
			var col2 = newRow.insertCell(1); // device ID
			var col3 = newRow.insertCell(2); // Size (GB)
			var col4 = newRow.insertCell(3); // checkbox
			
			col1.innerHTML=nodeName;
			col2.innerHTML=devID;
			col3.innerHTML=devSize;
			checkBox = "<input type='checkbox' name='selectDisk' id='" +nodeName + "_" + devID + "'/>"
			col4.innerHTML=checkBox;
		}
	}
	document.getElementById('registerBricks').className = 'registerButton';
	
}

function selectAll() {
	// flip all 
	if (document.getElementById('allDisks').checked == true) {
		updateCheckbox('selectDisk',true)
	}
	else {
		updateCheckbox('selectDisk',false)
	}
	
}


function findDisks() {
	//alert('run get disks process')
	
	showBusy('Scanning nodes for unused disks');
	
	xml_http_post('../www/main.html', 'findDisks', showDisks);
	
	
}

function registerHandler(req) {

	response = req.responseText;
	if (response == 'OK') {
		slide('disks','bricks');
	}
	
	// trigger slide transition to build bricks page
	
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
		var callerParms = '<disks>';
		var numBricks = 0;
		
		for (var n = 0; n<numCheckboxes; n++ ) {
			
			if (checkboxes[n].checked) {
				numBricks++;
				var idName = checkboxes[n].id;
				var part = idName.split('_');
				var nodeName = part[0];
				var devID = part[1];
				
				callerParms = callerParms + "<device host='" + nodeName + "' device='" + devID +"' />"
			}
		}
		callerParms = callerParms + '</disks>';
		callerString = 'registerBricks|' + callerParms;
		// showBusy('Creating 	' + numBricks + ' bricks');
		
		xml_http_post('../www/main.html', callerString, registerHandler);
	
	}
	
	
	// if not, do nothing
	

	
}
