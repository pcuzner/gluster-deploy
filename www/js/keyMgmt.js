

function startKeyMgmt() {
	showBusy();
	
	// populate the div with the nodes
	
	// alert('these are the nodes to act upon' + glusterNodes.join());
	
	keysTable = document.getElementById("keysTable");
	
	for (var n=0; n<glusterNodes.length; n++) {
		thisNode = glusterNodes[n];
		// need to add code to define a class for the row to highlight
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

function keyResponse() {
	// receive a nodename and a response - success or fail
	// if good, then add this node to the keyAdded array
	//	else add to the keyFailed array
	
	// check size of the keyAdded + keyFailed array - 
	// 		if it matches the size of the glusterNodes array - we're done
	//			update the spinner indicating success/failure
	//			update the text
	//			activate button if all successful
}

function pushKeys() {
	// 1st validate the keys
	//	if valid carry on, if not then do nothing

	passwordType = document.querySelector('input[name="passwordMethod"]:checked').value;
	
	if (keysValid(passwordType) ) {
		alert('keys are ok to use');
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
