
var glusterNodes = new Array(); 

var pageError=false;	// boolean used to catch validation on pages

var brickList = {}; 	/* Assoc. Array, indexed by the server:/brick syntax */

var MAXREPLICA = 2;
var RAWGB = 0;
var BRICKSUSED = 0;

pollingInterval = 1500; 	// ms polling delay used by queryMsgs

var msgLog = new Array();	// array holding status messages from the server 


/* Brick Object creator Method */
function Brick(svr, fsname, size) {
	this.server=svr;
	
	// If the svr contains a '.' then it's fully qualified, so create a
	// short version for display purposes
	if ( svr.indexOf('.') > 0 ) {
		this.shortName = svr.split('.')[0];
	}
	else {
		this.shortName = svr;
	}
	
	this.fsname=fsname;
	this.sizeGB = parseInt(size);
	this.brickPath=svr + ":" + fsname;
	this.selected= false;

}
