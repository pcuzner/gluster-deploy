

function fade(elementName,state) {
	
	// Give state a default to disable the element
	var state = state || 'disable'
	
	// Toggle the fade attribute of the given element
	
	if (document.getElementById(elementName).className == 'fade') {
		document.getElementById(elementName).className ='';
	}
	else {
		document.getElementById(elementName).className ='fade'
		
		if (state == "disable") {
			disableDiv(elementName)
		}
	}
}

function disableDiv(divName) {
	// Disable the div first
	document.getElementById(divName).disabled = true;
	
	// now loop through the other elements in the div and disable them 
	var nodes = document.getElementById(divName).getElementsByTagName('*');
	for(var i = 0; i < nodes.length; i++) {
		nodes[i].disabled = true;
	}
}

function slide(oldDiv, newDiv) {

	document.getElementById(newDiv).className = 'slide';
	
	if ( newDiv != 'error' ) {
		// Update the menu area
		var oldTask = 'm-' + oldDiv
		var newTask = 'm-' + newDiv
		document.getElementById(oldTask).className = 'done';
		document.getElementById(newTask).className = 'active';
	}
	
	disableDiv(oldDiv);
	
}

function showBusy(msg) {
	
	var msg = msg || '';
	document.getElementById('busyMsg').innerHTML = msg;
	if (document.getElementById('busy').style.visibility == 'visible') {
		document.getElementById('busy').style.visibility = 'hidden';
		document.getElementById('busyGraphic').className = 'spinner';
		document.getElementById('busyButton').disabled = true;
		document.getElementById('busyButton').style.visibility = 'hidden';
	}
	else {
		document.getElementById('busy').style.visibility = 'visible';
	}
	
}

function enableButton(buttonName) {

	document.getElementById(buttonName).disabled = false;
}

function updateCheckbox(checkboxName, state) {
	
	
	// function that just toggles the checked state of all checkboxes in a given group
	var checkboxes = document.getElementsByName(checkboxName);
	var numCheckboxes = checkboxes.length;
	
	for (var i=0; i<numCheckboxes; i++) {
		checkboxes[i].checked = state;
	}
		
}


function disableRadio(radioName) {
	radioButtons = document.getElementsByName(radioName);
	numButtons = radioButtons.length;
	for (var n =0; n < numButtons; n++) {
		radioButtons[n].disabled = true;
	}
}

function toggleElement(elementName) {
	// Simply toggle the disabled true or false of a given element
	currentState = document.getElementById(elementName).disabled; 
	document.getElementById(elementName).disabled = !currentState; 
}


function formatGB(gb) {
	// Receive a GB value, scale it and add a t or g suffix
	if (gb < 1000) {
		val = gb + "g"
	}
	else {
		val = (gb/1000);
		val = val.toFixed(1) + "t"
	}
	return val;
}

function emptyTable(tableName) {
	// Receive a table name, and then delete the rows in it
	thisTable = document.getElementById(tableName);
	
	// find the number of table rows
	var numRows = (thisTable.tBodies[0].rows.length) - 1;

	// loop, deleting these rows (except for 1st row)		
	for ( var i= numRows; i>0; i--) {
		thisTable.deleteRow(i)
	}
	
	// empty the data from the first cell		
	thisTable.rows[0].cells[0].innerHTML = " ";
	
}

function countSelected(elementName) {
	// Return the number of selected items in a given list/selectbox
	var options = document.getElementById(elementName).options;
	var count = 0;
	for ( var i = 0; i< options.length; i++) {
		
		if (options[i].selected) {
			//alert(options[i].value + " .. " + count);
			count = count + 1;
		}
	}

	return count
}

function removeSelected(selectBox) {
	// remove any selected item in the given "select box"
	thisBox = document.getElementById(selectBox)
	
	for (var i = thisBox.options.length-1; i>=0; i--) {
		if (thisBox.options[i].selected == true) {
			thisBox.remove(i);
		}
	}
}

function shutDown() {
	// Send a quit message to the python web server to shut down 
	// the script
	
	xml_http_post('../www/main.html', 'quit', dummyHandler);
}

function dummyHandler(req) {
	resp = req.responseText;
}

function showMountHelp() {
	window.location = ('../www/mounthelp.html');
	shutDown();
}

function finish() {
	//document.getElementById('quitButton').disabled = true;
	parent = document.getElementById('finish');
	child = document.getElementById('quitButton');
	parent.removeChild(child);
	
	link = document.getElementById('mountHelp'); 
	link.removeAttribute('href');
		
	document.getElementById('goodbye').className = 'reveal';
	shutDown();
}
