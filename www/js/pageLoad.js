if (window.addEventListener) { // Mozilla, Netscape, Firefox
    window.addEventListener('load', pageLoad, false);
} else if (window.attachEvent) { // IE
    window.attachEvent('onload', pageLoad);
}

function pageLoad() {
	document.getElementById('checkKey').disabled = false;
	document.getElementById('overviewNext').disabled=true;
}

