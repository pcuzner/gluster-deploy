
var glusterNodes = new Array();


var brickList = {}; 	/* Assoc. Array, indexed by the server:/brick */

var MAXREPLICA = 2;
var RAWGB = 0;
var BRICKSUSED = 0;


/* Brick Object creator Method */
function Brick(svr, fsname, size) {
	this.server=svr;
	this.fsname=fsname;
	this.sizeGB = parseInt(size);
	this.brickPath=svr + ":" + fsname;
	this.selected= false;
}
