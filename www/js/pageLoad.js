


if (window.addEventListener) { // Mozilla, Netscape, Firefox
    window.addEventListener('load', pageLoad, false);
} else if (window.attachEvent) { // IE
    window.attachEvent('onload', pageLoad);
}

function pageLoad() {
	document.getElementById('checkKey').disabled = false;
	
	// Not needed since the divs are now loaded dynamically.
	// document.getElementById('overviewNext').disabled=true;
}

