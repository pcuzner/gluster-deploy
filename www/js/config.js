
var glusterNodes = new Array(); 

var pageError=false;			// boolean used to catch validation on pages



var MAXREPLICA = 2;
var RAWGB = 0;
var BRICKSUSED = 0;
var glusterSnapshots = false;	// flag set when node versions are compared
								// at the server

var pollingInterval = 1000; 	// ms polling delay used by queryMsgs

var msgLog = new Array();		// array holding status messages from the server 

var currentPage = '';			// string used to track the current page in the UI


var brickList = {}; 			// Assoc. Array, indexed by the server:/brick syntax 

/* Brick Object creator Method */
function Brick(svr, fsname, size) {
	this.server=svr;
	this.fsname=fsname;
	this.sizeGB = parseInt(size);
	this.brickPath=svr + ":" + fsname;
	this.selected= false;

}

var glusterVolumeList = {}; 	// Assoc. Array, indexed by volume name 

/* Volume Object creator */
function GlusterVolume(volName, useCase, mountPoint, volType, nfs, cifs, brickListStr) {
	this.volumeName = volName;
	this.useCase = useCase;
	this.mountPoint = mountPoint;
	this.volumeType = volType; 
	this.nfsEnabled = nfs;			// boolean
	this.cifsEnabled = cifs;		// boolean
	this.brickList = brickListStr;

}
