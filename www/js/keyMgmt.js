

function startKeyMgmt() {
	showBusy();
	
	// populate the div with the nodes
	
	keysTable = document.getElementById("keysTable");
	
	for (var n=0; n<glusterNodes.length; n++) {
		thisNode = glusterNodes[n];
		
		var newRow = keysTable.insertRow(-1);
		var col1 = newRow.insertCell(0);
		var col2 = newRow.insertCell(1);
		col1.innerHTML=thisNode;
		boxName = thisNode + "-pswd"
		inputBox = '<input type="text" id="' + boxName + '" disabled size="16">'
		col2.innerHTML=inputBox;
		
	}
	
	
	slide('keys');
	
	document.getElementById('busyButton').style.visibility = 'hidden';
	document.getElementById('busyGraphic').className = 'spinner';
	
}


function boxesHidden(state) {
	
	for (var n=0; n<glusterNodes.length; n++) {
		thisNode = glusterNodes[n];
		elementName = thisNode + '-pswd';
		document.getElementById(elementName).disabled = state;
	}	
}

function togglePassword(passwordType) {
	
	if (passwordType == 'generic') {
		document.getElementById('genericPassword').style.visibility = 'visible';
		boxesHidden(true);
	}
	else {
		document.getElementById('genericPassword').style.visibility = 'hidden';
		
		// show the password boxes
		boxesHidden(false);
	}

}

function keyHandler(req) {
	
	xmlDoc = req.responseXML;
	var state = xmlDoc.getElementsByTagName("status-text")[0].childNodes[0].nodeValue;
	var success = xmlDoc.getElementsByTagName("summary")[0].getAttribute("success");
	var failed = xmlDoc.getElementsByTagName("summary")[0].getAttribute("failed");

	document.getElementById('busyMsg').innerHTML = "Key Distribution Complete<br>" +
													"Successful: " + success + " Failures: " + failed;

	if ( state == 'OK' ) {
		
		// Setup the next DIV
		populateDiv(xmlDoc);
		
		// change the spinner to a green tick
		document.getElementById('busyGraphic').className = 'success';																								
		document.getElementById('busyButton').disabled = false;
		document.getElementById('busyButton').style.visibility = 'visible';
		document.getElementById('busyButton').onclick = function() { startDiskDiscovery();};

	}
	else {
		// change the spinner to a warning sign
		document.getElementById('busyGraphic').className = 'fail';

	}
}

function pushKeys() {
	// 1st validate the keys
	//	if valid carry on, if not then do nothing

	passwordType = document.querySelector('input[name="passwordMethod"]:checked').value;
	
	if (keysValid(passwordType) ) {
		
		showBusy('Distributing SSH keys');
		document.getElementById('pushKeys').disabled = true;
		document.getElementById('genericPassword').disabled = true;
		
		// Disable the radio Buttons
		disableRadio('passwordMethod');

		
		var xmlString = "<data><request-type>push-keys</request-type>";
		
		if (passwordType == 'generic') {
			thisPassword = document.getElementById('genericPassword').value;
		}
		
		numNodes = glusterNodes.length;
		for (var n=0; n < numNodes; n++) {
			nodeName = glusterNodes[n];
			if (passwordType == 'generic') {
				nodePassword = thisPassword;
			}
			else {
				boxName = nodeName + "-pswd";
				nodePassword = document.getElementById(boxName).value;
			}
			
			xmlString = xmlString + "<node server='" + nodeName + "' password='" + nodePassword + "' />";
		}
	
	
	
		xmlString = xmlString + "</data>";

	
		// pass back to python to execute peer probe
		xml_http_post('../www/main.html', xmlString, keyHandler);		
	}
	else {
		alert('You must supply a valid password for the node(s)');
	}
	
}

function keysValid(passwordType) {
	// if generic password selected - ensure the password field is not blank
	
	// validate the password 
	
	rc = true;
	
	if (passwordType == 'generic') {
		if (document.getElementById('genericPassword').value.length == 0) {
			document.getElementById('genericPassword').className = 'error';
			rc = false;
		}
		else { // user selected generic password and provided a password
			rc = true;
			document.getElementById('genericPassword').className = '';
		}
	}
	else { // each node in the table must have a password provided

		numNodes = glusterNodes.length;
		for (var n=0; n < numNodes; n++) {
			boxName = glusterNodes[n] + '-pswd';
			thisPassword = document.getElementById(boxName).value;
			if (thisPassword.length == 0) {
				document.getElementById(boxName).className = 'error';
				rc = false;
			}
			else {
				document.getElementById(boxName).className = '';
			}
			
		}
		
		
		
	}
	return rc	

}
