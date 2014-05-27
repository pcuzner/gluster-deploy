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
	local pathName=$2
	local cmd="umount $pathName"

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
	
	if [ $node != 'localhost' ]; then 
		conn="ssh $node"
	fi


	# lvremove /dev/vg/lv --> does not remove the thinpool
	# lvremove lv --> does remove thinpool and lv

	cmd="vgremove -f $vg"
	cmdOut=$($pfx $conn $cmd 2>&1)
	rc=$?
	fmtCmdOut "$cmdOut"
	#cont=false

	#if [ $rc -eq 0 ]; then 

		## lv removed OK, but need to check if lv has a pool to remove
		## that as well.
		#if [ -n "$pool" ]; then 
			#cmd="lvremove -f /dev/$vg/$pool"
			#cmdOut=$($pfx $conn $cmd 2>&1)
			#rc=$?
			#fmtCmdOut "$cmdOut"
		#fi
		
		#echo "acting on vg >$vg< and pv >$pv<"
		#cmd="vgreduce $vg $pv"
		#cmdOut=$($pfx $conn $cmd 2>&1)
		#case $? in
			#0) 
				#echo -e "\t\tRemoving $pv from Volume Group $vg"
				#fmtCmdOut "$cmdOut"
				#cont=true
				#;;
			
			##   Can't remove final physical volume "bla" from volume group "wah"
			## or
			##   Physical volume "/dev/vdb" still in use 
			#5)	
				#echo -e "\t\tRemoving volume group $vg"
				#cmd="vgremove $vg"
				#cmdOut=$($pfx $conn $cmd 2>&1)
				#rc=$?
				#if [ $rc -eq 0 ] ; then 
					#fmtCmdOut "$cmdOut"
					#cont=true
				#fi
				#;;

			#*)	fmtCmdOut "$cmdOut"
				#rc=99
				#;;

		#esac
		
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
	
	if [ "$target" != "localhost" ]; then 
		conn="ssh $target "
	fi

	# Create a backup copy of fstab...just in case!
	cmd="/bin/cp -f /etc/fstab /etc/fstab_saved"

	echo -e "\t\tSaving the current fstab to /etc/fstab_saved"
	$pfx $conn $cmd 
	
	echo -e "\t\tRemoving the fstab entry for $pathName in fstab"
	cmd="sed -n -i '\,$pathName,"'!p'"' /etc/fstab"

	# If this is the localhost, run the command directly
	if [ "$target" == "localhost" ] ; then
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
		local brickPath=$2		
		unset IFS

		if [ $node == $thisHost ] ; then 
			node='localhost'
		fi

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
		
		dropNode $node || return $?

		removeSSH $node || return $?

	done
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
		if [ $node == $thisHost ]; then 
			echo $2
			break
		fi
		unset IFS
	done

}

function getLV {
	# Look in the mount table for a given brick path to find the associated lv
	# output is written directly to stdout	
	
	local node=$1
	local pathName=$2
	
	if [ $node != 'localhost' ]; then 
		ssh $node "awk -v fs=$pathName '{ if(\$2 == fs) { print \$1;}}' /proc/mounts"
	else
		awk -v fs=$pathName '{ if($2 == fs) { print $1;}}' /proc/mounts	
	fi

}

function getPool {
	# get the poolname. Using xargs as a simple way to trim leading/trailing whitespace
	local node=$1
	local lv=$2
	
	if [ $node != 'localhost' ]; then 
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
	if [ $node != 'localhost' ]; then 
		ssh $node "vgs $vg -o pv_name --noheadings | xargs"	
	else
		vgs $vg -o pv_name --noheadings | xargs
	fi
}

function getVG {
	local node=$1
	local lv=$2

	if [ $node != 'localhost' ] ; then 
		ssh $node "lvs $lv --noheadings -o vg_name | xargs"
	else 
		lvs $lv --noheadings -o vg_name | xargs
	fi
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

	volList=$(gluster vol list 2>&1)
	
	#brickList=$(gluster vol status $volName | tr ":" " " | awk '/Brick/ {print $3;}')
	brickList=$(gluster vol status $volName | awk '/^Brick/ {print $2;}')
	if [ -z "$brickList" ] ; then
			echo "-> Volume '$volName' does not exit. undodeploy.sh run aborted"
			exit 12
	fi
	
	localBrick=$(getLocalBrick "$brickList")
	
	lvName=$(getLV 'localhost' $localBrick)

	vgName=$(getVG 'localhost' $lvName)

 	brickType=$(awk -v fs=$localBrick '{ if($2 == fs) { print $3;}}' /proc/mounts)
	
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
