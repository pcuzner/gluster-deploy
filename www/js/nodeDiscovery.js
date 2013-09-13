
function startNodesPage() {
	// drop the access/password layer right back out of the way
	document.getElementById('access').style.zIndex=-99;

	// call ajax to get list of networks available
	xml_http_post('../www/main.html','subnetList', subnetSetup);
	
	slide("overview","nodes") ;
}

function subnetSetup(req) {
	
	// request returns a string containing subnets separated by spaces
	// split this into an array and update the pulldown
	subnetString =req.responseText;
	subnet = subnetString.split(" "); 
	
	dropdown = document.getElementById("network-select");
	
	// If we have subnets to select, populate the pulldown and enable the 
	// button
	if (subnet.length > 0) {
		
		for (var n=0; n<subnet.length; ++n) {
			dropdown[dropdown.length] = new Option(subnet[n]);
		}
		
		document.getElementById('network-scan-btn').disabled = false;
	}
}
function nodeSelect(req) {
	// display the nodes discovered
	
	// turn off the showbusy spinner
	showBusy();
	
	//document.getElementById('network-scan-btn').disabled = false;
	document.getElementById('nodeSelect').className = 'show';
	
	var nodes = req.responseText;
	nodeList = nodes.split(" ");
	candidate = document.getElementById('candidateNodes') ;
	selected = document.getElementById('selectedNodes') ;
	if (nodeList.length > 0) {
		for (var n=0; n<nodeList.length; ++n) {
			
			// if the node name has a '*' suffix place it in the selected box, 

			if (nodeList[n].indexOf('*') != -1) {
				
				// add node to the selected box
				selected[selected.length] = new Option(nodeList[n]);
				//selected.options[selected.length].disabled = true;
			}
			else {
				//this host is not the host we're running on so add to candidate box
				candidate[candidate.length] = new Option(nodeList[n]);
			}
		}
	}
	
}

function scanSubnet() {
	// grab the current value from the pulldown list
	// ajax call 'findNodes'
	targetSubnet = document.getElementById('network-select').value;
	document.getElementById('network-select').disabled=true;
	document.getElementById('network-scan-btn').disabled = true;
	showBusy('Scanning ' + targetSubnet);
	callerString = "findNodes|" + targetSubnet;
	xml_http_post('../www/main.html', callerString, nodeSelect);
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

function clusterHandler(req) {
	// Handle the response from creating a cluster
	// turn off show busy
	// showBusy(); // turn show busy off
	
	// [0] = success, [1] failed
	var respData = req.responseText.split(' ');

	var failed = parseInt(respData[1]);

	document.getElementById('busyMsg').innerHTML = "Cluster created<br>" +
													"Successful: " + respData[0] + " Failures: " + respData[1];
	if (failed > 0) {
		document.getElementById('busyGraphic').className = 'error';
		// change the spinner to a warning sign
		alert('Problems creating the cluster\nPlease Investigate');
	}
	else {
		document.getElementById('busyGraphic').className = 'success';
		// change the spinner to a green tick
																										
		document.getElementById('busyButton').disabled = false;
		document.getElementById('busyButton').style.visibility = 'visible';
		document.getElementById('busyButton').onclick = function() { startKeyMgmt();};
		document.getElementById('selectedNodes').disabled = true;
		

		
		
	}
		

	//document.getElementById('keysNext').style.visibility = 'visible';
	//document.getElementById('keysNext').disabled = false;


}

function createCluster() {

	// disable the candidate and selected boxes
	document.getElementById('addNodes').disabled = true;
	document.getElementById('createCluster').disabled = true;
	document.getElementById('candidateNodes').disabled = true;
	selected = document.getElementById('selectedNodes');

	
	var nodesString = "";
	var nodeCount = 0;
	
	for (var n = 0 ; n < selected.options.length; n++) {
		thisNode = selected.options[n].value; 
		if (thisNode.indexOf("*") == -1) {
			nodesString = nodesString + thisNode + " ";
			glusterNodes.push(thisNode)
			nodeCount +=1;
		}
	}

	showBusy('Adding ' + nodeCount + ' nodes') ;	
	
	callerString = 'createCluster|' + nodesString.trim() ;

	// pass back to python to execute peer probe
	xml_http_post('../www/main.html', callerString, clusterHandler);

		
}
