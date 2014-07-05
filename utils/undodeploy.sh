#!/bin/bash
#
# Script used during testing to tear down config.
#
# ***************************************************************
# * WARNING                                                     *
# * This script is for testing purposes ONLY and is intended to *
# * be used to enable quicker testing of the gluster-deploy.py  *
# * tool.   													*
# * 															*
# * It has been tested on cluster that use DNS for the gluster  *
# * peers only - using it for an IP based cluster will not end  *
# * well!														*
# *                                                             *
# * YOU HAVE BEEN WARNED!                                       *
# *                                                             *
# ***************************************************************
#
# 1 brick = 1 LV = 1 VG = 1 PV .... nice and (over?) simple!
#
# This script must run on the host that initially performed the 'deploy'
# since it relies on the passwordless ssh that deploy sets up, to drop
# the gluster configuration
#

function usage {
	echo -e "\nUsage: $prog "
	echo -e "This script will 'undo' a configuration defined by the gluster-deploy.py tool."
	echo -e "\nIt accepts the following arguments;"
	echo -e "\t-h ... displays this usage information"
	echo -e "\t-d ... DEBUG mode, just displays the commands that would be executed"
	echo -e "\nNB. The gluster volume must be in a started state for this script to work correctly."

}


function unmountFS {
	local target=$1
	local pathName=$2
	
	local cmd="ssh $target umount $pathName"

	echo -e "\t\tUnmounting filesystem $pathName on $target"

	$pfx $cmd	
	
}

function fmtCmdOut {
	# function that receives command output and splits into an array (by \n)
	# to keep the output formatting sequence correct

	local cmdOutput="$1"			# Needs quotes since string will contain spaces

	readarray -t output <<<"$cmdOutput"
	
	for line in "${output[@]}"; do
		echo -e "\t\t-->$line"
	done
}
	

function dropLVM {
	# 1 LUN = 1 VG = 1 Brick
	# for a thin vol, you can't easily determine the associated pv
	# so to keep things simple - dropping the vg with force

	local node=$1
	local lv=$2
	local conn=""
	local cmdOut=""

	local vg=$(getVG $node $lv)
	local pv=$(getPV $node $vg)


	
	echo -e "\t\tRemoving LVM definitions(LV and VG)"
	
	cmd="ssh $node vgremove -f $vg"
	cmdOut=$($pfx $cmd 2>&1)
	rc=$?
	fmtCmdOut "$cmdOut"
		
	if [ $rc -eq 0 ] ; then 
		echo -e "\t\tWiping PV label from device(s)"
		cmd="ssh $node pvremove $pv"
		cmdOut=$($pfx $cmd)
		rc=$?
		fmtCmdOut "$cmdOut"
	fi
			
	return $rc
}

function tunedReset {
	local target=$1
	
	echo -e "\t\tResetting tuned profile to 'default' on $target"
	cmd="ssh $target tuned-adm profile default 2>&1"
	resp=$($pfx $cmd)
	rc=$?
	
	fmtCmdOut "$resp"
	

	return $rc
}



function fstabUpdate {
	local target=$1
	local pathName=$2
	local cmd=""
	local conn=""
	

	# Create a backup copy of fstab...just in case!
	cmd="ssh $target /bin/cp -f /etc/fstab /etc/fstab_saved"

	echo -e "\t\tSaving the current fstab to /etc/fstab_saved"
	$pfx $conn $cmd 
	
	echo -e "\t\tRemoving the fstab entry for $pathName in fstab"
	cmd="ssh $target sed -n -i '\,$pathName,"'!p'"' /etc/fstab"

	$pfx $cmd
	
	echo -e "\t\tRemoving directory $pathName on $target"
	cmd="ssh $target rm -fr $pathName"
	
	$pfx $cmd

}

function dropVolume {
	local volume=$1
	local cmd=""
	local cmdOut=""
	local rc=0

	echo -e "\t-> Stopping volume '$volName'..."
	cmd="yes | gluster vol stop $volume force 2>&1"
	cmdOut=$($pfx eval $cmd )
	rc=$?
	fmtCmdOut "$cmdOut"
	
	if [ $rc -eq 0 ] ; then 
		# delete the volume
		echo -e "\t-> Deleting volume '$volName'..."
		cmd="yes | gluster vol del $volName 2>&1"
		cmdOut=($pfx eval $cmd)
		fmtCmdOut "$cmdOut"
		rc=$?
	fi


	return $rc
}



function dropNode {
	local node=$1
	local cmd=""
	local cmdOut=""

	if [ "$node" == "localhost" ]; then 
		echo -e "\t\tSkipping peer detach for the local peer"
		return 0
	else
		echo -e "\t\tRemoving $node from the cluster"	
		
		cmd="gluster peer detach $node"
	
		cmdOut=$($pfx $cmd 2>&1)
		fmtCmdOut "$cmdOut"		
	fi
	

}

function removeSSH {
	local node=$1
	local cmd=""
	local conn=""

	# We only have to remove the keys for the remote hosts, so if this is the
	# local machine, just return to the caller
	if [ "$node" == "localhost" ] ; then 
		echo -e "\t\tRemoving ssh keys skipped (not applicable on local node)"
		return 0
	fi
	
	conn="ssh $node"
	echo -e "\t\tRemoving ssh keys from node $node"
	cmd="sed -n -i '/root@$node/"'!p'"' /root/.ssh/authorized_keys"

	# Execute the commands built inside the variables
	$pfx $conn $cmd
	
}

function umountVolume {
	local volName=$1
	
	mountState=$(grep $volName /proc/mounts)
	
	if [ $? -eq 0 ] ; then 
		# all mount points will be the same since this is gluster-deploy 
		# based config
		
		local mountPath=$(echo $mountState | cut -d " " -f 2)
		echo "$volName will be unmounted from all systems"
		
		for peer in "${nodeList[@]}"; do 
			
			# 1. issue the umount
			unmountFS $peer $mountPath
			
			# 2. update fstab
			fstabUpdate $peer $mountPath
		
			
		done
		
	else
		echo -e "\t'$volName' is not mounted on the local node, skipping umount logic"
	fi 
	


}

function getBrickType {
	local volName=$1
	local brickType="xfs"
	
	brickType=$(gluster vol status $volName detail | grep "File System" | head -n 1 | cut -d ":" -f 2 | sed 's/^ *//')
	
	echo $brickType
}


function resetCluster {

	# flag set by each volume to determine the brick provider
	# xfs = lvm, or btrfs
	local brickType='xfs'

	# check for the presense of snapshots - any snapshots will cause the
	# script to abort
	if $snapshotsAvailable ; then 
		local snapList=$(gluster snap list)
		if [ "$snapList" != "No snapshots present" ]; then
			echo "undodeploy can not continue - one or more volumes still have snapshots"
			echo "associated with them.Remove the snapshots, and then rerun this tool."
			return 12
		fi 
	fi
	
	local -a brickPaths

	echo -e "\nRemoving volume(s)...prepare for mind-wipe!"
	
	# process each volume in volList
	for volName in "${volList[@]}"; do 

		# get the type of brick provider used for the volumes bricks
		brickType=$(getBrickType $volName)
		echo -e "\nProcessing volume '$volName'"

		# unmount the volume if mounted on the nodes		
		# assumption is that deploy mounts a volume to all nodes, so the 
		# presence on this node, means it has to be done across all nodes 
		# and remove any mount setting from fstab 
		umountVolume $volName || return $?
				
		dropVolume $volName || return $?
	

		
		unset IFS
		read -a brickPaths <<< ${vol2Bricks[$volName]}
		echo -e "\tRemoving bricks"
		
		for brickInfo in "${brickPaths[@]}"; do 
	
			IFS=":"
			set -- $brickInfo
			local node=$1
	
			local brickPath=$(dirname $2)		
			unset IFS
	
			echo -e "\t- Processing peer '$node'"
	
			# It's important to perform the get lv before the unmount
			# or we lose the x-ref between mountpoint and device
			lvName=$(getLV $node $brickPath)
	
			unmountFS $node $brickPath || return $?
	
			fstabUpdate $node $brickPath || return $?
			
			
			case "$brickType" in 
				xfs)
					dropLVM $node $lvName || return $?
					;;
				btrfs)	
					echo "Not ready for btrfs YET!"
					return 20
					;;
	 		esac
	
		done
	done

	# At this point each volume has been deleted, bricks unmount, LVM configs
	# dropped and fstabs updated
	# Next up is to remove the ssh keys from the other nodes in the cluster
	echo -e "\n\tResetting tuned, removing ssh keys and peer membership"
	for peer in "${nodeList[@]}"; do 
		
		echo -e "\n\tProcessing node $peer"
		tunedReset $peer || return $?
		
		removeSSH $peer || return $?
		
		dropNode $peer || return $?

	done


}


function snapsOK {
	resp=true
	local snapPGM=$(rpm -ql glusterfs | grep snap)
	if [ -z $snapPGM ]; then
		resp=false
	fi

	echo    $resp

}



function getLV {
	# Look in the mount table for a given brick path to find the associated lv
	# output is written directly to stdout	
	
	local node=$1
	local mountPoint=$2

	ssh $node "awk -v fs=$mountPoint '{ if(\$2 == fs) { print \$1;}}' /proc/mounts"
}


	
function getPV {
	# receive a vg and return the associated PV
	# assumes 1 PV = 1 VG
	
	local node=$1
	local vg=$2
	
	ssh $node "vgs $vg -o pv_name --noheadings | xargs"	
}

function getVG {
	local node=$1
	local lv=$2

	ssh $node "lvs $lv --noheadings -o vg_name | xargs"

}


function main {
	
	
	# Define associative array to track bricks belonging to a volume
	declare -A vol2Bricks
	
	snapshotsAvailable=$(snapsOK)
	
	read -a nodeList <<< $(gluster peer status | awk '/Hostname:/ {print $2;}')
	nodeList[${#nodeList[*]}]='localhost'
	
	pfx=""					# pfx is only set in debug mode to show
							# commands instead of executing them 

	numNodes=${#nodeList[@]}
	
	DEBUG=false

	while getopts ":dh" OPT; do
		case "$OPT" in
			h)
				usage
				return 20
				;;
			d)
				DEBUG=true
				;;
			#v)
			#	volName=$OPTARG
			#	;;

			\?)
				echo -e "\t- Unknown option provided -$OPTARG"
				usage
				return 16
				;;

			:)
				echo -e "\t- Option -$OPTARG requires an argument."
				return 12
				;;
		esac
	done

	if $DEBUG; then 
		echo -e "\n--> Running in debug mode <--\n"
		pfx='echo >>> DEBUG - Cmd to execute : '
	fi


	unset IFS
	read -a volList <<< $(gluster vol list 2>&1)
	
	if [ -z "$volList" ]; then 
		echo "-> No volumes exist in this configuration"
		exit 12
	fi
	
	allVolumes=${#volList[@]}
	allBricks=0
	
	
	echo -e "\nAnalysing each volume in the cluster"
	for volName in "${volList[@]}"; do 
		vol2Bricks[$volName]=$(gluster vol status $volName | awk '/^Brick/ {print $2;}'); 
		read -a bricks <<< ${vol2Bricks[$volName]}
		let allBricks=$allBricks+${#bricks[@]}
	done
	
	echo -e "Actions to undertake are as follows;"
	echo -e "\t- stop and delete $allVolumes gluster volume(s)"
	echo -e "\t- unmount and delete $allBricks brick configurations"
	echo -e "\t- drop the trusted pool ($numNodes nodes)"
	echo -e "\t- remove all associated LVM definitions for the bricks"
	echo -e "\t- remove fstab entries for filesystems used by the bricks and volumes"

	while true; do
		read -r -p "Are you Sure (y/n)?" confirm
		case $confirm in 
			y|Y) 	goAhead=true
					break
					;;
			n|n) 	goAhead=false
					break
					;;
		esac
		echo ""
	done
	
	if $goAhead ; then 

		resetCluster ||  return $?

	else
		echo -e "\n\nRun Aborted by user"
		return 8
	fi
	
}

prog=$(basename $0)
echo -e "\n$prog starting"
main "$@";
echo -e "\n$prog finished - highest RC = $?"
