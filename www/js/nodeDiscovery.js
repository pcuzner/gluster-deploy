
function startNodesPage() {
	// drop the access/password layer right back out of the way
	document.getElementById('access').style.zIndex=-99;			

	var xmlString = "<data><request-type>subnet-list</request-type></data>";

	// Make a call back to the host, and set up response handler
	xml_http_post('../www/main.html',xmlString, subnetSetup);
	
	slide("overview","nodes") ;
}

function subnetSetup(req) {
	
	xmlDoc = req.responseXML;
	
	// request returns a string containing subnets separated by spaces
	// split this into an array and update the pulldown
	// subnetString =req.responseText;
	// subnet = subnetString.split(" "); 
	
	var state = xmlDoc.getElementsByTagName("status-text")[0].childNodes[0].nodeValue;
	
	if ( state == 'OK' ) {
		subnets = xmlDoc.getElementsByTagName('subnet');		// array of subnet elements
		dropdown = document.getElementById("network-select");
		
		// If we have subnets to select, populate the pulldown and enable the 
		// button
		if (subnets.length > 0) {
			
			for (var n=0; n<subnets.length; n++) {
				
				dropdown[dropdown.length] = new Option(subnets[n].childNodes[0].nodeValue);
			}
			
			document.getElementById('network-scan-btn').disabled = false;
		}
	}
	else {
		// insert error handler here!
	}
	
}

function nodeSelect(req) {
	// display the nodes discovered
	
	// turn off the showbusy spinner
	showBusy();
	
	xmlDoc = req.responseXML;
	var state = xmlDoc.getElementsByTagName("status-text")[0].childNodes[0].nodeValue;
	
	if ( state == "OK" ) {
		var nodes = xmlDoc.getElementsByTagName('node');	// Get all node elements from XML
	
		document.getElementById('nodeSelect').className = 'show';

		candidate = document.getElementById('candidateNodes') ;
		selected = document.getElementById('selectedNodes') ;
		if (nodes.length > 0) {
			for (var n=0; n<nodes.length; n++) {
	
				var nodeName = nodes[n].childNodes[0].nodeValue;
				
				// if the node name has a '*' suffix place it in the selected box, 
				if (nodeName.indexOf('*') != -1) {
					
					// add node to the selected box
					selected[selected.length] = new Option(nodeName);
	
				}
				else {

					//this host is not the host we're running on so add to candidate box
					candidate[candidate.length] = new Option(nodeName);
				}
			}
		}
	}
	else {
		// insert error handler here!
	}
}

function scanSubnet() {
	// grab the current value from the pulldown list
	// ajax call 'findNodes'
	targetSubnet = document.getElementById('network-select').value;
	document.getElementById('network-select').disabled=true;
	document.getElementById('network-scan-btn').disabled = true;
	showBusy('Scanning ' + targetSubnet);
	
	var xmlString = "<data><request-type>find-nodes</request-type><subnet>" + targetSubnet +"</subnet></data>";
	
	xml_http_post('../www/main.html', xmlString, nodeSelect);
	
	enableMsgLog();

}


function promoteNodes() {
	
	// move the nodes from candidate to selected nodes
	var candidate = document.getElementById('candidateNodes');
	var selected = document.getElementById('selectedNodes');
	
	// Copy the selected items over to the selected box
	for (var n = 0; n < candidate.options.length; n++) {
		if (candidate.options[n].selected == true) {
			selected[selected.length] = new Option(candidate.options[n].value);
		}
	}	
	
	// remove the items copied from the candidate box (must be done bottom up!)
	for (var n=candidate.options.length-1; n >=0; n--) {
		if (candidate.options[n].selected == true) {
			candidate.remove(n);
		}
	}
	
	// enable the create cluster button
	document.getElementById('createCluster').disabled = false;	
	
	// if the select nodes box is empty, disable the add nodes button
	if (candidate.options.length == 0) {
		document.getElementById('addNodes').disabled=true;
	}
}

// TODO - make this handler generic to be used for cluster, key and disk summary

function clusterHandler(req) {

	xmlDoc = req.responseXML;
	
	var state = xmlDoc.getElementsByTagName("status-text")[0].childNodes[0].nodeValue;
	var success = xmlDoc.getElementsByTagName("summary")[0].getAttribute("success");
	var failed = xmlDoc.getElementsByTagName("summary")[0].getAttribute("failed");

	if ( state == "OK" ) {
		
		// Add the nodes passed back as successful, to an array (used by keyMgmt.js)
		var nodes = xmlDoc.getElementsByTagName('node');
		for (var i=0; i< nodes.length; i++) {
			var thisNode = nodes[i].getAttribute('name');
			glusterNodes.push(thisNode);
		}
	
		document.getElementById('busyMsg').innerHTML = "Cluster created<br>" +
														"Successful: " + success + " Failures: " + failed;
		// change the spinner to a green tick
		document.getElementById('busyGraphic').className = 'success';

																										
		document.getElementById('busyButton').disabled = false;
		document.getElementById('busyButton').style.visibility = 'visible';
		document.getElementById('busyButton').onclick = function() { startKeyMgmt();};
		document.getElementById('selectedNodes').disabled = true;
			
	}
	else {
		// cluster create failed error
		document.getElementById('busyGraphic').className = 'fail';
		// change the spinner to a warning sign
		alert('! Problems encountered !\nCheck the log file');

	}
		

}

function createCluster() {

	// disable the candidate and selected boxes
	disableDiv('nodes');
	
	selected = document.getElementById('selectedNodes');

	
	var nodesString = "";
	
	var xmlString = "<data><request-type>create-cluster</request-type>";
	
	for (var n = 0 ; n < selected.options.length; n++) {
		thisNode = selected.options[n].value; 
		
		xmlString = xmlString + "<node>" + thisNode + "</node>";
				
	}
	
	// Just use the number of items in the select box - local node to 
	// describe the number of nodes to peer probe.
	showBusy('Adding ' + ( selected.options.length - 1) + ' nodes') ;	
	
	xmlString = xmlString + "</data>";
	
	// pass back to python to execute peer probe
	xml_http_post('../www/main.html', xmlString, clusterHandler);

		
}
