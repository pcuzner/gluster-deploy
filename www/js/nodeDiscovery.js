
function startNodesPage() {
	// drop the access/password layer right back out of the way
	document.getElementById('access').style.zIndex=-99;			

	var xmlString = "<data><request-type>subnet-list</request-type></data>";

	// Make a call back to the host, and set up response handler
	xml_http_post('../www/main.html',xmlString, subnetSetup);
	

}

function subnetSetup(req) {
	
	xmlDoc = req.responseXML;
	
	var state = xmlDoc.getElementsByTagName("status-text")[0].childNodes[0].nodeValue;
	var requestType = xmlDoc.getElementsByTagName("request-type")[0].childNodes[0].nodeValue;
	
	if ( state == 'OK' ) {
		
		populateDiv(xmlDoc);
		
		slide("nodes") ;
		
		switch(requestType) {
			case "scan" :
		
				subnets = xmlDoc.getElementsByTagName('subnet');		// array of subnet elements
				dropdown = document.getElementById("network-select");	// DOM element on the page
				
				// If we have subnets to select, populate the pulldown and enable the 
				// button
				if (subnets.length > 0) {
					
					for (var n=0; n<subnets.length; n++) {
						dropdown[dropdown.length] = new Option(subnets[n].childNodes[0].nodeValue);
					}
					
					document.getElementById('network-scan-btn').disabled = false;
				}
				
				break;
				
			case "servers":
			
					// turn of the subnet select elements
					disableDiv("nodeScanning");
					document.getElementById("nodeScanning").className = 'hidden';
					document.getElementById("nodesProvided").className = "show";
					
					// turn on the text to describe the servers are provided by config file override
					// turn on the candidate and select nodes div
					document.getElementById('nodeSelect').className = 'show';
					scanSubnet('serverlist');

					break;
		}		
	}
	else {
		// insert your error handler here!
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

function scanSubnet(scanType) {
	
	scanType = typeof scanType !== "undefined" ? scanType : "subnet" ;
	
	switch(scanType) {
		case "subnet":
		
			// grab the current value from the pulldown list
			targetSubnet = document.getElementById('network-select').value;
			disableDiv("nodeScanning");
			
			showBusy('Scanning ' + targetSubnet);
			
			var xmlString = "<data><request-type>find-nodes</request-type><scan-type>subnet</scan-type><subnet>" + targetSubnet +"</subnet></data>";
			

			
			break;
			
		case "serverlist":
		
			showBusy('Checking servers provided');
			var xmlString = "<data><request-type>find-nodes</request-type><scan-type>serverlist</scan-type></data>";
			
			break;
			
	}
	
	// Make call back to webserver, and set up the nodeSelect as the handler for the response		
	xml_http_post('../www/main.html', xmlString, nodeSelect);
		
	// Invoking a scan is a long running task, so enable the MsgLog to get progress
	// updates
	if ( scanType == 'subnet' ) {
		enableMsgLog();
	}
		

	

}


//function promoteNodes() {
	
	//// move the nodes from candidate to selected nodes
	//var candidate = document.getElementById('candidateNodes');
	//var selected = document.getElementById('selectedNodes');
	
	//// Copy the selected items over to the selected box
	//for (var n = 0; n < candidate.options.length; n++) {
		//if (candidate.options[n].selected == true) {
			//selected[selected.length] = new Option(candidate.options[n].value);
		//}
	//}	
	
	//// remove the items copied from the candidate box (must be done bottom up!)
	//for (var n=candidate.options.length-1; n >=0; n--) {
		//if (candidate.options[n].selected == true) {
			//candidate.remove(n);
		//}
	//}
	
	//// enable the create cluster button
	//document.getElementById('createCluster').disabled = false;	
	
	//// if the select nodes box is empty, disable the add nodes button
	//if (candidate.options.length == 0) {
		//document.getElementById('addNodes').disabled=true;
	//}
//}

function moveNodes(source, target) {
	// function to move nodes between the candidate and selected boxes
	// and vice-versa

	// static references to the candidate and selected boxes
	var candidate = document.getElementById('candidateNodes');
	var selected = document.getElementById('selectedNodes');
	
	
	var inbox = document.getElementById(source);
	var outbox = document.getElementById(target);
	
	// Copy the selected items over to the selected box
	for (var n = 0; n < inbox.options.length; n++) {
		if (inbox.options[n].selected == true) {
			var nodeSelected = inbox.options[n].value;
			if (nodeSelected.slice(-1) == '*') {
				inbox.options[n].selected = false;
			}
			else {
				outbox[outbox.length] = new Option(inbox.options[n].value);
			}
		}
	}
	
	// remove the items copies from the source box
	for (var n=inbox.options.length-1; n >=0; n--) {
		if (inbox.options[n].selected == true) {
			inbox.remove(n);
		}
	}

	// Handle the enabled/disabled state of the add/remove nodes 
	// buttons
	if (candidate.options.length == 0) {
		document.getElementById('addNodes').disabled=true;
	}
	else {
		document.getElementById('addNodes').disabled=false;
	}
	
	if (selected.options.length == 1) {
		document.getElementById('rejectNodes').disabled=true;
	}
	else {
		document.getElementById('rejectNodes').disabled=false;
	}
	
	
	// disable the create cluster button if there aren't any nodes in the 
	// 'nodes selected' box
	if (selected.options.length > 1) {
		document.getElementById('createCluster').disabled = false;
	}
	else {
		document.getElementById('createCluster').disabled = true;
	}
	
}


function clusterHandler(req) {

	xmlDoc = req.responseXML;
	
	var state = xmlDoc.getElementsByTagName("status-text")[0].childNodes[0].nodeValue;
	var success = xmlDoc.getElementsByTagName("summary")[0].getAttribute("success");
	var failed = xmlDoc.getElementsByTagName("summary")[0].getAttribute("failed");

	if ( state == "OK" ) {
		
		// get the next page info, and populate the div
		populateDiv(xmlDoc);
		
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
	showBusy('Adding ' + ( selected.options.length - 1) + ' node(s)') ;	
	
	xmlString = xmlString + "</data>";
	
	// pass back to python to execute peer probe
	xml_http_post('../www/main.html', xmlString, clusterHandler);

		
}
