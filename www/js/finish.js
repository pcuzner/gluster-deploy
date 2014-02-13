// *************************************************************
// * these functions handle the final page(s) of the deploy UI *
// *************************************************************

function showFinish(state) {
	showBusy(); // turn off the showbusy message

	if ( state == 'OK') {
		// activate finish div	
		slide('volCreate','finish');
	}
	else {
		//activate the error page
		slide('volCreate','error');
		shutDown();
	}

}
