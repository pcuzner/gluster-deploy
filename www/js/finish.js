// *************************************************************
// * these functions handle the final page(s) of the deploy UI *
// *************************************************************

function getSummary() {

	// invoke the finish call back to the server to get a
	// summary of what was done
		
	var xmlString = "<data><request-type>finish</request-type></data>";
	
	xml_http_post('../www/main.html', xmlString, showSummary);

}

function showSummary(req) {
	
	var xmlDoc = req.responseXML;
	var msg = xmlDoc.getElementsByTagName("message");
	var summary = document.getElementById('tasksummary');
	var taskSummary = "";
	
	for (var i=0; i<msg.length; i++) {
		msgText = msg[i].childNodes[0].nodeValue
		taskSummary += "<li class='icon-ok'>" + msgText + "</li>"
	}

	summary.innerHTML = taskSummary;
	
	// check if the current UI page is the volume create step to 
	// determine if the closing remarks needs to change
	if ( currentPage != "volCreate") {
		var nextSteps = document.getElementById('nextsteps');
		terminationMsg = "<p>You have chosen to terminate the deploy wizard early.</p>"
		terminationMsg += "<p>You may now complete the remaining steps for your configuration manually.</p>"
		
		nextSteps.innerHTML = terminationMsg
	}

	slide('finish');
	
}
