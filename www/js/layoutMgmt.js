

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
	var oldTask = 'm-' + oldDiv
	var newTask = 'm-' + newDiv
	document.getElementById(oldTask).className = 'done';
	document.getElementById(newTask).className = 'active';
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
