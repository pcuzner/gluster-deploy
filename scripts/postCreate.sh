#!/bin/bash

# postCreate.sh
#
# Return Codes
# 0  .. All good
# 16 .. action definition not defined, don't know what to do for that!
#
# Change History
# ../06/2014 Created
#
# Future Changes
# 1. ?
# 

function updateFSTAB {

	# using /bin/cp since cp is normally an alias of cp -i
	/bin/cp /etc/fstab /etc/fstab_backup
	
	if [ "$?" -eq 0 ]; then 
		echo "$nodeName:/$volumeName    $mountPoint    glusterfs    defaults,_netdev 0 0" >> /etc/fstab
		rc=$?
	fi
	return $rc
}


function mountVolume {

	# mkdir will work even if the dir already exists
	mkdir -p $mountPoint

	updateFSTAB || return $?
	
	# with the glusterfs entry added, issue mount to
	#   a) ensure fstab is OK, 
	#   b) get the volume mounted!
	/bin/mount -a -t glusterfs

}


function dump_parms {

	logger "postCreate.sh invoked as follows;"
	logger "dryrun 		: $dryrun"
	logger "Action Type : $action"
	logger "Mount Point : $mountPoint"
	logger "Volume      : $volumeName"
	logger "Node        : $nodeName"

}




function main {
	
	local rc=0
	local debug=false
	
	args=("$@")
	logger "postCreate.sh - Invocation parms: $args"
	
	while getopts "Dta:m:v:n:" OPT; do
		case "$OPT" in
			D)
				debug=true
				;;
			t)
				dryrun=1
				;;
			a)
				action=$OPTARG
				;;
			m)	
				mountPoint=$OPTARG
				;;
			v)	
				volumeName=$OPTARG
				;;
			n)	
				nodeName=$OPTARG
				;;			

			:)
				echo "Option -$OPTARG requires an argument."
				;;
		esac
	done
	
	if [ $debug ]; then 
		dump_parms
	fi
	
	logger "postCreate.sh - processing started"
	
	
	case "$action" in 
		mount)
				mountVolume
				rc=$?
				;;
			*)
				logger "postCreate.sh - Unknown action provided - aborting"
				rc=16
				;;
	esac
	
	logger "postCreate.sh processing finished - RC=$rc"
	exit $rc
	
}

main "$@";

