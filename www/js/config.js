
var glusterNodes = new Array(); 

var pageError=false;	// boolean used to catch validation on pages

var brickList = {}; 	/* Assoc. Array, indexed by the server:/brick syntax */

var MAXREPLICA = 2;
var RAWGB = 0;
var BRICKSUSED = 0;

var pollingInterval = 1000; 	// ms polling delay used by queryMsgs

var msgLog = new Array();		// array holding status messages from the server 

var currentPage = '';			// string used to track the current page in the UI

/* Brick Object creator Method */
function Brick(svr, fsname, size) {
	this.server=svr;
	this.fsname=fsname;
	this.sizeGB = parseInt(size);
	this.brickPath=svr + ":" + fsname;
	this.selected= false;

}
