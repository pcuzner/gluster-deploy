

function startKeyMgmt() {
	showBusy();
	
	// populate the div with the nodes
	
	// alert('these are the nodes to act upon' + glusterNodes.join());
	
	keysTable = document.getElementById("keysTable");
	
	for (var n=0; n<glusterNodes.length; n++) {
		thisNode = glusterNodes[n];
		
		// TODO - tr css class has a highlight, so could use it here when building the table
		
		var newRow = keysTable.insertRow(-1);
		var col1 = newRow.insertCell(0);
		var col2 = newRow.insertCell(1);
		col1.innerHTML=thisNode;
		boxName = thisNode + "-pswd"
		inputBox = '<input type="text" id="' + boxName + '" disabled size="16">'
		col2.innerHTML=inputBox;
		
	}
	
	
	slide('nodes','keys');
	
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

function keyHandler() {

	showBusy();
	
}

function pushKeys() {
	// 1st validate the keys
	//	if valid carry on, if not then do nothing

	passwordType = document.querySelector('input[name="passwordMethod"]:checked').value;
	
	if (keysValid(passwordType) ) {
		alert('keys are ok to use');
		
		showBusy('Distributing SSH keys');
		
		var keyData = '';
		
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
			keyData = keyData + " " + nodeName + "*" + nodePassword; 
		}
	
		
		
		callerString = 'pushKeys|' + keyData.trim() ;
	
		// pass back to python to execute peer probe
		xml_http_post('../www/main.html', callerString, keyHandler);		
	}
	else {
		alert('keys are duff');
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
