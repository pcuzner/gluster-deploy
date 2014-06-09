
/*
	This code segment defines the actions that provide the brick management 
	logic                                                                   
*/

function updateSnapshot() {
	num = document.getElementById('snapshotSpace').value;
	document.getElementById('snapshotValue').innerHTML = num.toString() + "%";
}

function snapshotWarning(req) {
	var xmlDoc = req.responseXML;
	
	populateDiv(xmlDoc);
	
	showModal('on');
}


function buildBricks() {
	// gather the values from the prompts and check to see if a confirmation 
	// dialog is needed
	
	if (! pageError) {

		var brickProvider = document.getElementById('brickProvider').value;
		
		// turn boolean value into yes or no
		var snapRequired = (document.getElementById('snapshotsRequired').checked ? 'YES' : 'NO');
		
		// Issue a warning dialog, of the gluster environment does not support snapshots
		// but a brick config that supports snapshots has been selected by the user.
		if ((( snapRequired == 'YES') || ( brickProvider == 'BTRFS')) && (! glusterSnapshots)) {
			
			// Confirmation is required to use these features. Using the js confirm dialog, is the
			// easiest way to do this, but the look and feel is not consistent with the UI's theme.
			// Instead we'll use a couple of div elements configured to provided the same modal window
			// interaction, which allows the UI theme to be applied for a consistent look and feel.
			
			// Add text to the modal title div
			//document.getElementById('modal-title').innerHTML = '<h3>Experimental Features Selected</h3>';
			
			//// add text to the modal text div area
			//var mdContent = "<p>Enabling snapshot support through the Logical Volume Manager ";
			//mdContent +=    "or the 'btrfs' filesystem are features that are still under development.</p>";
			//mdContent +=    "<p>They are included to enable easier testing of these features within ";
			//mdContent +=    "the glusterfs developer community, and are therefore not suitable for ";
			//mdContent +=    "production deployments</p>";
			//mdContent +=    "<p>By clicking 'OK' bricks will be configured with these experimental features enabled.</p>"; 

			//document.getElementById('modal-text').innerHTML = mdContent;
			
			//// setup the buttons in the modal window to call appropriate function
			//document.getElementById('modal-btn-cancel').onclick = function(){ showModal(); } ;
			//document.getElementById('modal-btn-ok').onclick = function(){ showModal(); buildFmtRequest(); };

			var xmlString = "<data><request-type>get-modal</request-type>"
			xmlString += 	"<page-request htmlfile='www/modal-snapshot-warning.html' />"
			xmlString +=	"</data>"
			
			xml_http_post('../www/main.html', xmlString, snapshotWarning);

		
		}
		else {
			buildFmtRequest();
		}

	}

}

function buildFmtRequest() {
	
	document.getElementById('buildBricks').disabled=true;	// turn the button off
	document.getElementById('useCase').disabled=true; 		// turn off the pulldown selection
	
	
	// Extract the settings from the UI page
	var snapRequired = (document.getElementById('snapshotsRequired').checked ? 'YES' : 'NO');
	var brickProvider = document.getElementById('brickProvider').value;	
	var useCase = document.getElementById('useCase').value;
	var snapshotReserve = document.getElementById('snapshotSpace').value;
	var volumeGroup = document.getElementById('vgName').value;
	var lvName = document.getElementById('lvName').value;
	var mountPoint = document.getElementById('mountPoint').value;

	// Create XML string to initiate the brick formatting process	
	var xmlString = "<data><request-type>build-bricks</request-type><brickparms usecase='" + useCase + "' ";
	xmlString += "brickprovider='" + brickProvider + "' ";
	xmlString += "snaprequired='" + snapRequired + "' ";
	
	if ( snapRequired == 'YES') {
		xmlString += "snapreserve='" + snapshotReserve.toString() + "' ";
	}
	
	if ( brickProvider == 'LVM' ) {
		xmlString += "lvname='" + lvName + "' ";
		xmlString += "volgroup='" + volumeGroup + "' ";				
	}

	// if the 'tuned' pulldown is active, grab the current setting and pass back
	if (document.getElementById('tunedProfile').length > 0) {
		xmlString += "tuned='" + document.getElementById('tunedProfile').value + "' ";
	}
	


	xmlString += "mountpoint='" + mountPoint + "'/></data>";
	
	showBusy('Creating Bricks');
	

	// Pass the string back to the server
	xml_http_post('../www/main.html', xmlString, bricksDefined);
	
	setTimeout(enableMsgLog,400);
}



function bricksDefined(req) {

	var xmlDoc = req.responseXML;
	
	var state = xmlDoc.getElementsByTagName("status-text")[0].childNodes[0].nodeValue;
	
	/* req is an xml string defining the bricks just created in the format
	 	<data>
			<summary success='6' failed='0' />"
				<brick fsname='/gluster/brick' size='10' servername='rhs1-1' />
				<brick fsname='/gluster/brick2' size='10' servername='rhs1-1' />				  
		</data>
	*/
	
	if ( state == 'OK' ) {
		document.getElementById('busyGraphic').className = 'success';
		
		// Set up the volCreate Page
		populateDiv(xmlDoc);
		
		
		// populate the brick list
		var brick = xmlDoc.getElementsByTagName("brick");
		var brickPool = document.getElementById("brickPool");
		
		for (var i=0 ; i< brick.length; i++ ) {
			var svr = brick[i].getAttribute("servername");
			var gb  = brick[i].getAttribute("size");
			var fsname = brick[i].getAttribute("fsname");
			
			var thisBrick = new Brick(svr,fsname,gb);
			var key = svr + ":" + fsname;
			
			brickList[key] = thisBrick;
			
		}
			
		populateBrickPool();
	}
	else {
		document.getElementById('busyGraphic').className = 'fail';
	}
																										
	document.getElementById('busyButton').disabled = false;
	document.getElementById('busyButton').style.visibility = 'visible';
	document.getElementById('busyButton').onclick = function() { showVolCreate(state);};	
	
}
function showVolCreate(state) {
	
	showBusy(); // Turn off the showbusy spinner
	
	if ( state == 'OK' ) {
		slide('volCreate'); // slide the volcreate page into view


	}
	else {
		// build brick hit errors
		slide('error');
		shutDown();
	}
}

function snapToggle(snapRequired) {
	if ( snapRequired ) {
		// show the snap reserve range selector
		document.getElementById('snapReserve').className='show';
	}
	else {
		// hide the range selector
		document.getElementById('snapReserve').className='';
		document.getElementById('snapshotSpace').value = 10;
		// reset the current value to default (10)
	}
	
}

function validateBrickParms(element) {
	// Perform basic validation checks on the data received from the user
	// to improve the likelihood of success in the brickFormat.sh script
	
	var validLVM = /^[a-zA-Z][-a-zA-Z0-9\_]*$/
	var validMountPoint = /^\/[a-z0-9\/]*$/
	
	var thisElement = element.id;
	var thisValue = document.getElementById(thisElement).value;
	
	switch (thisElement){
		case 'vgName':
		case 'lvName':
			var patternRegex = validLVM;
			break;
		case 'mountPoint':
			var patternRegex = validMountPoint
			break;
	}
	
	// Check the name adheres to the relevant standards
	if ( ! thisValue.match(patternRegex) ) {
		// null value, so the match failed, alert the user and flag error 
		document.getElementById(thisElement).className='brickInputField error';
		pageError=true;
	}
	else { 
		// add the default class back to reset the colors from any previous error
		document.getElementById(thisElement).className = 'brickInputField';
		pageError=false;
	}
}

function switchProvider(option) {
	
	if ( option == "BTRFS" ) {
		document.getElementById('lvm').className = 'hidden';
	}
	else {
		document.getElementById('lvm').className = '';
	}

}

function updateLV() {
	var vgName = document.getElementById('vgName').value;
	document.getElementById('lvName').value=vgName;
}





