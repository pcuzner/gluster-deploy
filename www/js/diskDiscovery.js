
// disk management

function startDiskDiscovery() {

	showBusy(); // turn of the busy dialog
	slide("keys","disks");
	
	
}

function showDisks(req) {
	showBusy();

	alert(req.responseText);
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
	var nodes = xmlDoc.getElementsByTagName('NODE');	// nodes is an array
	var numNodes = nodes.length;
	for (var n = 0 ; n< numNodes; n++) {
		var newRow = diskTable.insertRow(-1);
		var col1 = newRow.insertCell(0);
		var col2 = newRow.insertCell(1);
		var col3 = newRow.insertCell(2);
		var col4 = newRow.insertCell(3);
		col1.innerHTML=nodes[n].getElementsByTagName('NODENAME')[0].childNodes[0].nodeValue;
		col2.innerHTML=nodes[n].getElementsByTagName('DEVID')[0].childNodes[0].nodeValue;
		col3.innerHTML=nodes[n].getElementsByTagName('SIZE')[0].childNodes[0].nodeValue;
		col4.innerHTML='&nbsp';
		
	}
	
	
}


function getDisks() {
	//alert('run get disks process')
	
	showBusy('Scanning nodes for unused disks');
	
	xml_http_post('../www/main.html', 'getDisks', showDisks);
	
	// form a string of the nodes/password from the glusterNode objects
	// turn on showbusy
	// set message to 'scanning for disks'
	// pass string to server to process - handler is showDisks
	
}
