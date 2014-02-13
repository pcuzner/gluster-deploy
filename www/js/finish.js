// *************************************************************
// * these functions handle the final page(s) of the deploy UI *
// *************************************************************

function showFinish(state) {
	showBusy(); // turn off the showbusy message

	if ( state == 'OK') {
		// invoke the finish call back to the server to get a
		// summary of what was done
		
		var xmlString = "<data><request-type>finish</request-type></data>";
	
		xml_http_post('../www/main.html', xmlString, showSummary);
	
	}
	else {
		
		//activate the error page
		slide('volCreate','error');
		shutDown();
	}

}


function showSummary(req) {
	
	var xmlDoc = req.responseXML;
	var msg = xmlDoc.getElementsByTagName("message");
	var summary = document.getElementById('tasksummary');
	var taskSummary = "";
	
	for (var i=0; i<msg.length; i++) {
		taskSummary += "<li class='icon-ok'>" + msg[i].childNodes[0].nodeValue + "</li>"
	}
	
	summary.innerHTML = taskSummary;
	
	slide('volCreate','finish');
	
}
