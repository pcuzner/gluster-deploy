#!/bin/bash
#
# Script used during testing to tear down config.
#
# ***************************************************************
# * WARNING                                                     *
# * This script is for testing purposes ONLY and is intended to *
# * be used to enable quicker testing of the gluster-deploy.py  *
# * tool. Using this script to drop a configuration created by  *
# * another tool will likely result in errors and introduce the *
# * potential of data loss.                                     *
# *                                                             *
# * YOU HAVE BEEN WARNED!                                       *
# *                                                             *
# ***************************************************************
#
# Receive the volume to 'drop'
# Query gluster to get a list of the bricks in the volume
# Query gluster to get a list of nodes
# Query the host to determines the filsystem type of the bricks in the volume
# Drop the volume (stop and delete)
# Process each  node
# 	unmount the brick
#	remove from fstab
#	handle the brick filesystem
#		drop the associated VG (and LV)  OR
#		drop btrfs
# Drop the foreign nodes from the gluster cluster
# 


function usage {
	echo -e "\nUsage: $prog -v volume_name"
	echo -e "This script 'undoes' a configuration defined by the gluster-deploy.py tool."
	echo -e "\nIt accepts the following arguments;"
	echo -e "\t-h ... displays this usage information"
	echo -e "\t-v ... provides the volume name to drop"
	echo -e "\t-n ... NORUN mode, just displays the commands that would be executed"
	echo -e "\nNB. The gluster volume must be in a started state for this script to work correctly."

}


function unmountFS {
	local target=$1
	local cmd="umount $brickPath"

	echo -e "\t\tUnmounting brick filesystem on $target"
	if [ "$target" != "localhost" ] ; then
		cmd="ssh $target $cmd"
	fi

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
	local node=$1
	local conn=""
	local cmdOut=""
	
	echo -e "\t\tRemoving LVM definitions(LV and VG)"
	cmd="pvs | awk '\$2 ~ /^"$vgName"/ {print \$1;}'"

	if [ "$node" != "localhost" ] ; then 
		conn="ssh $node "
		local devList=$($conn $cmd)
	else
		local devList=$(pvs | awk "\$2 ~ /^$vgName/ { print \$1;}")
	fi
	

	cmd="vgremove $vgName -f"
	cmdOut=$($pfx $conn $cmd 2>&1)
	fmtCmdOut "$cmdOut"
	

	echo -e "\t\tWiping PV label from device(s)"
	cmd="pvremove $devList"
	cmdOut=$($pfx $conn $cmd 2>&1)
	fmtCmdOut "$cmdOut"

}

function dropBTRFS {
	local node=$1
}



function fstabUpdate {
	local target=$1
	local cmd=""
	local conn=""
	
	if [ "$target" != "localhost" ]; then 
		conn="ssh $target "
	fi

	# Create a backup copy of fstab...just in case!
	cmd="/bin/cp -f /etc/fstab /etc/fstab_saved"

	echo -e "\t\tSaving the current fstab to /etc/fstab_saved"
	$pfx $conn $cmd 
	
	echo -e "\t\tRemoving the fstab entry for $brickPath in fstab"
	cmd="sed -n -i '\,$brickPath,"'!p'"' /etc/fstab"

	# If this is the localhost, run the command directly
	if [ "$target" == "localhost" ] ; then
		sed -n -i '\,'$brickPath',!p' /etc/fstab	
	else
		# Execute the commands built inside the variables
		$pfx $conn $cmd
	fi

	$pfx $conn rm -fr "$brickPath"

}

function dropVolume {
	local cmd=""
	local cmdOut=""

	echo -e "Stopping volume $volName..."
	echo "y" | gluster vol stop $volName force 
	
	# This will cause a prompt to the user
	cmd="gluster vol del $volName"
	$pfx $cmd 

}

function getNodes {
	# Requires glusterfs 3.4+ for the gluster pool list command
	local nodes=$(gluster pool list | awk '/-/ { print $2; }')
	echo $nodes
}

function dropNode {
	local node=$1
	local cmd=""
	local cmdOut=""

	if [ "$node" == "localhost" ]; then 
		return 0
	fi

	echo -e "\t\tRemoving $node from the cluster"	
	
	cmd="gluster peer detach $node"

	cmdOut=$($pfx $cmd 2>&1)
	fmtCmdOut "$cmdOut"

}

function numItems {
	echo $#
	
}

function removeSSH {
	local node=$1
	local cmd=""
	local conn=""

	# We only have to remove the keys for the remote hosts, so if this is the
	# local machine, just return to the caller
	if [ "$node" == "localhost" ] ; then 
		echo -e "\t\tRemoving ssh keys skipped (no keys to remove on localhost)"
		return 0
	fi

	conn="ssh $node"

	echo -e "\t\tRemoving ssh keys"
	cmd="sed -n -i '/root@$thisHost/"'!p'"' /root/.ssh/authorized_keys"

	# Execute the commands built inside the variables
	$pfx $conn $cmd
	
}

function resetCluster {

	dropVolume || return $?

	echo "Removing node configuration settings..." 
	
	for node in $nodeList;  do

		echo -e "\n\tProcessing peer $node"

		unmountFS $node || return $?

		fstabUpdate $node || return $?
		
		case "$brickType" in 
			xfs)
				dropLVM $node || return $?
				;;
			btrfs)	
				dropBTRFS $node || return $?
				;;
 		esac
		
		dropNode $node || return $?

		removeSSH $node || return $?

	done
	
}
	

function main {
	
	thisHost=$(hostname -s)
	nodeList=$(getNodes)
	pfx=""					# pfx is only set in debug mode to show
						# commands instead of executing them 

	numNodes=$(numItems $nodeList) 
	
	NORUN=false

	while getopts ":nhv:" OPT; do
		case "$OPT" in
			h)
				usage
				return 20
				;;
			n)
				NORUN=true
				;;
			v)
				volName=$OPTARG
				;;

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

	if $NORUN; then 
		echo -e "\n--> Running in norun mode <--\n"
		pfx='echo >>> DEBUG - Cmd to execute : '
	fi

	
	if [ -z $volName ] ; then 
		echo -e "\t- not enough parameters supplied"
		return 4
	fi

	brickList=$(gluster vol status $volName | tr ":" " " | awk '/Brick/ {print $3;}')
	
	if [ -z "$brickList" ] ; then
			echo "-> Volume '$volName' does not exit. undodeploy.sh run aborted"
			exit 12
	fi
	
	
	
	
	# All bricks will be named the same for this volume, so use set to split the 
	# brickList string up into $1,$2 ... and then just use the first definition ($1)
	# e.g. 	brickList='/gluster/brick1 /gluster/brick1 /gluster/brick1'
	#      	becomes
	#		brickPath='/gluster/brick1'	
	set -- $brickList
	brickPath=$1

	lvName=$(grep $brickPath /proc/mounts | awk '{ print $1;}')
	vgName=$(lvs $lvName --noheadings | awk '{print $2;}')
 	brickType=$(awk -v fs=$brickPath '{ if($2 == fs) { print $3;}}' /proc/mounts)
	
	echo -e "Actions to undertake are as follows;"
	echo -e "\t- drop gluster volume called $volName"
	echo -e "\t- drop cluster definition ($numNodes nodes)"
	echo -e "\t- drop brick filesystem ($brickType)"
	echo -e "\t- drop associated LVM volume group ($vgName) and all associated LV's & PV's"
	echo -e "\t- remove fstab entries for filesystems used for the bricks"
	

	
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
		
		resetCluster

	else
		echo -e "\n\nRun Aborted by user"
		return 8
	fi
	
}

prog=$(basename $0)
echo -e "\n$prog starting"
main "$@";
echo -e "\n$prog finished - highest RC = $?"
