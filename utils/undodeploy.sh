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
	local volumePath=$2
	
	local cmd="umount $volumePath"

	echo -e "\t\tUnmounting brick filesystem on $target"
	if [ "$target" != $localNode ] ; then
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
	# 1 LUN = 1 VG = 1 Brick
	# for a thin vol, you can't easily determine the associated pv
	# so to keep things simple - dropping the vg with force

	local node=$1
	local lv=$2
	local conn=""
	local cmdOut=""

	local vg=$(getVG $node $lv)
	local pv=$(getPV $node $vg)

	#local pool=$(getPool $node $lv)
	
	echo -e "\t\tRemoving LVM definitions(LV and VG)"
	
	if [ $node != $localNode ]; then 
		conn="ssh $node"
	fi


	# lvremove /dev/vg/lv --> does not remove the thinpool
	# lvremove lv --> does remove thinpool and lv
	# vgremove with -f does BOTH which is what we want!

	cmd="vgremove -f $vg"
	cmdOut=$($pfx $conn $cmd 2>&1)
	rc=$?
	fmtCmdOut "$cmdOut"
		
	if [ $rc -eq 0 ] ; then 
		echo -e "\t\tWiping PV label from device(s)"
		cmd="pvremove $pv"
		cmdOut=$($pfx $conn $cmd)
		rc=$?
		fmtCmdOut "$cmdOut"
	fi
			
	#fi

	return $rc
}

function dropBTRFS {
	local node=$1
	# issue a "wipefs -a" against the devices
}



function fstabUpdate {
	local target=$1
	local pathName=$2
	local cmd=""
	local conn=""
	#local actualPath=$(dirname $pathName)
	
	
	if [ "$target" != $localNode ]; then 
		conn="ssh $target "
	fi

	# Create a backup copy of fstab...just in case!
	cmd="/bin/cp -f /etc/fstab /etc/fstab_saved"

	echo -e "\t\tSaving the current fstab to /etc/fstab_saved"
	$pfx $conn $cmd 
	
	echo -e "\t\tRemoving the fstab entry for $pathName in fstab"
	cmd="sed -n -i '\,$pathName,"'!p'"' /etc/fstab"

	# If this is the localhost, run the command directly
	if [ "$target" == $localNode ] ; then
		sed -n -i '\,'$pathName',!p' /etc/fstab	
	else
		# Execute the commands built inside the variables
		$pfx $conn $cmd
	fi

	$pfx $conn rm -fr "$pathName"

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



function dropNode {
	local node=$1
	local cmd=""
	local cmdOut=""

	if [ "$node" == $localNode ]; then 
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
	if [ "$node" == $localNode ] ; then 
		echo -e "\t\tRemoving ssh keys skipped (not applicable on local node)"
		return 0
	fi

	conn="ssh $node"

	echo -e "\t\tRemoving ssh keys"
	cmd="sed -n -i '/root@$thisHost/"'!p'"' /root/.ssh/authorized_keys"

	# Execute the commands built inside the variables
	$pfx $conn $cmd
	
}

function resetCluster {

	local brickPaths=($@)
	local lvName=""

	dropVolume || return $?

	echo "Removing node configuration settings..." 

	for brickInfo in "${brickPaths[@]}"; do 

		IFS=":"
		set -- $brickInfo
		local node=$1

		local brickPath=$(dirname $2)		
		unset IFS

		#if [ $node == $localNode ] ; then 
		#	node='localhost'
		#fi

		echo -e "\n\tProcessing peer $node"

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
				dropBTRFS $node || return $?
				;;
 		esac

		let disksProcessed[$node]=${disksProcessed[$node]}+1
		


		# if this is the last brick on this node, we can remove the ssh
		# keys and drop the node from the gluster config
		if [ ${disksProcessed[$node]} == ${totalDisks[$node]} ]; then 
			
			removeSSH $node || return $?
			
			dropNode $node || return $?
			
		else
			echo -e "\t\tBypassing ssh key removal, since more bricks to remove on this node($node)"
		fi
		

	done
}

function isName {
	local hostName=$1
	local re='^[0-9]'
	local char1=${hostName:0:1}
	local result=true
	
	if [[ $char1 =~ $re ]]; then 
			result=false
	fi
	
	echo $result
}



function isLocalHost {
	# function receiving a hostname, and returning whether that host
	# resolves to an IP on the local machine (boolean)
	
	local thisNode=$1

	if $(isName $thisNode); then 
		local target=$(host $thisNode | awk ' { print $4;}')
	else
		local target=$thisNode
	fi
	
	local IPonHost=$(ip addr show | grep $target)
	local resp=true

	if [ -z "$IPonHost" ]; then
		resp=false
	fi

	echo $resp
}




function getLocalBrick {

	# I assume that all the bricks across the cluster are formatted in a consistent 
	# manner by gluster-deploy, so I just need to find the first brick on the 
	# local node to determine the fs type...fstype then indicates whether this is
	# and lvm or btrfs environment

	local brickPaths=($@)
	for brick in "${brickPaths[@]}"; do
		IFS=":"
		set -- $brick
		node=$1
		if [ $node == $localNode ]; then
			local mountPath=$(dirname $2)
			echo $mountPath
			break
		fi
		unset IFS
	done

}

function getLV {
	# Look in the mount table for a given brick path to find the associated lv
	# output is written directly to stdout	
	
	local node=$1
	local mountPoint=$2
	#local mountPoint=$(dirname $pathName)
	
	if [ $node != $localNode ]; then 
		ssh $node "awk -v fs=$mountPoint '{ if(\$2 == fs) { print \$1;}}' /proc/mounts"
	else
		awk -v fs=$mountPoint '{ if($2 == fs) { print $1;}}' /proc/mounts	
	fi

}

function getPool {
	# get the poolname. Using xargs as a simple way to trim leading/trailing whitespace
	local node=$1
	local lv=$2
	
	if [ $node != $localNode ]; then 
		ssh $node "lvs $lv --noheading -o pool_lv | xargs"
	else
		lvs $lv --noheading -o pool_lv | xargs
	fi

}


	
function getPV {
	# receive a vg and return the associated PV
	# assumes 1 PV = 1 VG
	
	local node=$1
	local vg=$2
	if [ $node != $localNode ]; then 
		ssh $node "vgs $vg -o pv_name --noheadings | xargs"	
	else
		vgs $vg -o pv_name --noheadings | xargs
	fi
}

function getVG {
	local node=$1
	local lv=$2

	if [ $node != $localNode ] ; then 
		ssh $node "lvs $lv --noheadings -o vg_name | xargs"
	else 
		lvs $lv --noheadings -o vg_name | xargs
	fi
}


function getNodes {
	local nodes=$(gluster peer status | awk '/Hostname:/ { print $2; }')
	echo $nodes "localhost"
}

function createNodeCounters {
	# Sets up the associated arrays to track the number of bricks per node
	# and establishes which node is the localhost (localNode variable)
	
	local brickPath=($@)

	IFS=":"
	for brick in "${brickPath[@]}"; do
		set -- $brick
		local node=$1
		local path=$2

		local chkLocal=$(isLocalHost $node)
		if [ "$chkLocal" = true ]; then
			localNode=$node
		fi

		if [ -z ${totalDisks[$node]} ]; then
			totalDisks[$node]=1
			disksProcessed[$node]=0
		else
			let totalDisks[$node]=${totalDisks[$node]}+1
		fi

	done
	
	unset IFS
}



function main {
	
	
	# Define associative arrays to track the bricks by node for clusters that have 
	# more than one brick defined in a volume from a given node
	declare -A totalDisks
	declare -A disksProcessed

	localNode=''
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

	volList=$(gluster vol list 2>&1)
	
	#brickList=$(gluster vol status $volName | tr ":" " " | awk '/Brick/ {print $3;}')
	brickList=$(gluster vol status $volName | awk '/^Brick/ {print $2;}')
	if [ -z "$brickList" ] ; then
			echo "-> Volume '$volName' is not available. undodeploy.sh run aborted"
			exit 12
	fi
	
	# set the arrays to track bricks per node, and establish the node
	# from the brick list that is the local host
	createNodeCounters "$brickList"
	
	localBrick=$(getLocalBrick "$brickList")
	
	
	lvName=$(getLV $localNode $localBrick)
		

	vgName=$(getVG $localNode $lvName)

 	brickType=$(awk -v fs=$localBrick '{ if($2 == fs) { print $3;}}' /proc/mounts)
	
	echo -e "Actions to undertake are as follows;"
	echo -e "\t- drop gluster volume called '$volName'"
	echo -e "\t- drop cluster definition ($numNodes nodes)"
	echo -e "\t- drop brick filesystem ($brickType)"
	echo -e "\t- drop associated LVM volume group(s) and all associated LV's & PV's"
	echo -e "\t- remove fstab entries for filesystems used by the bricks"

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



		
		resetCluster "$brickList"

	else
		echo -e "\n\nRun Aborted by user"
		return 8
	fi
	
}

prog=$(basename $0)
echo -e "\n$prog starting"
main "$@";
echo -e "\n$prog finished - highest RC = $?"
