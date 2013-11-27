

function keyAction(req) {
	// xmlString = req.responseText;
	
	xmlDoc = req.responseXML;
	
	var state = xmlDoc.getElementsByTagName("status-text")[0].childNodes[0].nodeValue;
	
	if (state == "OK") {
		document.getElementById('password').className = '';
		fade('access');
		disableDiv('access');
			
		// Enable the next button and slide the overview page into view
		document.getElementById('overview').className = 'slide';
		document.getElementById('overviewNext').disabled = false;
		document.getElementById('m-overview').className='active';
	}
	else {
		// user suppled invalid password, so indicate the error
		document.getElementById('password').value = '';
		document.getElementById('password').className = 'error';
		document.getElementById('password').focus()
	}
		
}

function validateKey() {
	var userKey = document.getElementById('password').value ;
	
	var xmlString = "<data><request-type>password</request-type><password>" + userKey + "</password></data>";
	
	/*callerString = 'passwordCheck|' + xmlString; */
			
	/* xml_http_post('../www/main.html', callerString, keyAction); */
	xml_http_post('../www/main.html', xmlString, keyAction);	
		
}
