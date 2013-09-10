
/*  ajaxHandler.js
	JS to handle the ajax integration back to the web server 
	
*/

function xml_http_post(url, data, callback) {
    var request = false;
    try {
        // Firefox, Opera 8.0+, Safari
        request = new XMLHttpRequest();
    }
    catch (e) {
        // Internet Explorer
        try {
            request = new ActiveXObject("Msxml2.XMLHTTP");
        }
        catch (e) {
            try {
                request = new ActiveXObject("Microsoft.XMLHTTP");
            }
            catch (e) {
                alert("Your browser does not support AJAX!");
                return false;
            }
        }
    }
    request.open("POST", url, true);
    request.onreadystatechange = function() {
		// State 4 = complete, status 200 = Success (eg could be a 404)
        if (request.readyState == 4 && request.status == 200) {
            callback(request);
        }
    }
    request.send(data);
}
