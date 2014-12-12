
var glusterNodes = new Array(); 

var pageError=false;			// boolean used to catch validation on pages

var consoleOK = (typeof console != "undefined") ? true : false; 

var debugON = true;

var MAXREPLICA = 3;
var	TOTALBRICKS = 0;
//var RAWGB = 0;
//var BRICKSUSED = 0;
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
	this.queued=false;

}

var glusterVolumeList = {}; 	// Assoc. Array, indexed by volume name 

/* Volume Object creator */
function GlusterVolume(volName, useCase, target, mountPoint, volType, nfs, cifs, brickListStr, raw, usable, replica, hadoopPath) {
	this.volumeName = volName;
	this.useCase = useCase;
	this.target = target;
	this.mountPoint = mountPoint;
	this.volumeType = volType; 
	this.nfsEnabled = nfs;			// boolean
	this.cifsEnabled = cifs;		// boolean
	this.brickList = brickListStr;
	this.rawGB = raw;
	this.usableGB = usable;
	this.replicaCount = replica;
	this.hadoopMountPoint = hadoopPath;
	
	
	this.rowOutput = function() {
		var tdString = "";
		
		var numBricks = this.brickList.split(',').length;
		var faultTolerance = (this.volumeType == "Replicated") ? "Single Node" : "None";
		tdString += "<td>" + this.volumeName + "</td>";
		tdString += "<td>" + numBricks + "</td>";
		tdString += "<td>" + this.rawGB + "</td>";
		tdString += "<td>" + this.usableGB + "</td>";
		tdString += "<td>" + faultTolerance + "</td>";
	
		return tdString;
		
	}
	
	this.dumpXML = function() {
		
		var xmlString = "";
		
		xmlString += "<volume>";
		xmlString += "<settings name='" + this.volumeName + "' type='" + this.volumeType + "' ";
		xmlString += "replica='" + this.replicaCount + "' usecase='" + this.useCase + "' ";
		xmlString += "voldirectory='" + this.mountPoint + "' />";
		xmlString += "<protocols nfs='" + this.nfsEnabled.toString() + "' cifs='" + this.cifsEnabled.toString + "' />";
		
		xmlString += "<usecase>"
		switch(this.useCase.toLowerCase()) {
			case "virtualisation":
				xmlString += "<virttarget>" + this.target + "</virttarget>";
				break;
			case "hadoop":
				xmlString += "<hadooppath>" + this.hadoopMountPoint + "</hadooppath>";
				break;
				
		}
		xmlString += "</usecase>"
		
		xmlString += "<bricklist>";
		var volBricks = this.brickList.split(',');
		for (idx in volBricks) {
			xmlString += "<brick fullpath='" + volBricks[idx] + "' />";
		}
		xmlString += "</bricklist>";
		xmlString += "</volume>";
		
		return xmlString;

	}
}
