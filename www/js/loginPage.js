
function validateKey() {
	var userKey = document.getElementById('password').value ;
	
	/* if (userKey != accessKey) {
		// user suppled invalid password, so indicate the error
		document.getElementById('password').value = '';
		document.getElementById('password').className = 'error';
		document.getElementById('password').focus()
	}
	else {
	*/
	
		document.getElementById('password').className = '';
		fade('access');
		disableDiv('access');
		

		
		// Enable the next button and slide the overview page into view
		document.getElementById('overview').className = 'slide';
		document.getElementById('overviewNext').disabled = false;
		document.getElementById('m-overview').className='active';
	// }
}
