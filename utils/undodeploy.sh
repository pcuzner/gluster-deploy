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
# Process each 'foreign' node
# 	unmount the brick
#	drop the associated VG (and LV)
#   remove the brick from the fstab
# Repeat above 3 steps for the local node
# Drop the foreign nodes from the gluster cluster
# 



function unmountFS {

	echo "Unmounting brick filesystems"
	for node in $nodeList; do
		echo -e "\tUnmounting $brickPath on node $node"
		ssh $node umount $brickPath
	done
}

function dropLVM {
	
	echo -e "\nDropping volume group definitions"
	for node in $nodeList; do 
		local devList=$(ssh $node pvs | awk "/$vgName/ {print \$1;}")
		echo -e "- processing node $node"
		ssh $node vgremove $vgName -f
		for dev in $devList; do 
			echo "- removing device $dev from LVM control"
			ssh $node pvremove $dev
		done
			
	done

}

function fstabUpdate {
	
	echo -e "\nRemoving the brick entry from remote fstab's"
	for node in $nodeList; do 
	  ssh $node /bin/cp -f /etc/fstab /etc/fstab_saved
	  
	  uuid=$(ssh $node blkid $lvName | tr '"' ' '| awk '{print $3;}')
	  echo -e "- updating /etc/fstab on $node (backup in fstab_saved)"
	  # ssh $n sed -n -i "/$s/\!p" /root/testfile
	  ssh $node sed -n -i '/'$uuid'/!p' /etc/fstab 
	  ssh $node rm -fr "$brickPath"
	done 

}

function localUpdates {
	
	local devList=$(pvs | awk "/$vgName/ {print \$1;}")
	local uuid=$(blkid $lvName | tr '"' ' '| awk '{print $3;}')
	
	echo -e "\nProcessing local node"
	umount $brickPath
	echo "- removing volume group $vgName"
	vgremove $vgName -f
	
	for dev in $devList; do
		echo "- removing device $dev from LVM control"
		pvremove $dev
	done
	
	echo -e "- Backing up local fstab"
	/bin/cp -f /etc/fstab /etc/fstab_saved

	echo -e "- Removing brick entry from fstab"
	sed -n -i '/'$uuid'/!p' /etc/fstab
	echo -e "- Removing brick dir root"
	rm -fr $brickPath
}

function dropVolume {
	echo "Stopping volume $volName..."
	echo "y" | gluster vol stop $volName force
	
	echo "Deleting the volume"
	# This will cause a prompt to the user
	gluster vol del $volName
}

function getNodes {
	local nodes=$(gluster peer status | awk '/Hostname/ {print $2;}')
	echo $nodes
}

function dropNodes {

	echo -e "\nDropping nodes from the gluster cluster"	
	for node in $nodeList; do
		echo "- dropping $node"
		gluster peer detach $node
	done
}

function numItems {
	echo $#
	
}

function resetCluster {

	dropVolume || return $?
	
	unmountFS || return $?
	
	fstabUpdate || return $?
	
	dropLVM || return $?
	
	localUpdates || return $?
	
	dropNodes || return $?
}
	

function main {
	
	thisHost=$(hostname -s)
	nodeList=$(getNodes)

	numNodes=$(numItems $nodeList) 
	
	while getopts ":v:" OPT; do
		case "$OPT" in
			v)
				volName=$OPTARG
				;;

			\?)
				echo -e "\t- Unknown option provided -$OPTARG"
				return 16
				;;

			:)
				echo -e "\t- Option -$OPTARG requires an argument."
				return 12
				;;
		esac
	done
	
	if [ -z $volName ] ; then 
		echo -e "\t- not enough parameters supplied"
		return 4
	fi

	brickList=$(gluster vol status $volName | tr ":" " " | awk '/Brick/ {print $3;}')
	#brickList='/gluster/brick1 /gluster/brick1 /gluster/brick1'
	set -- $brickList
	brickPath=$1
	#brickPath='/gluster/brick1'

	lvName=$(grep $brickPath /proc/mounts | awk '{ print $1;}')
	vgName=$(lvs $lvName --noheadings | awk '{print $2;}')

	echo -e "Actions to undertake are as follows;"
	echo -e "\t- drop gluster volume called $volName"
	echo -e "\t- drop cluster definition ($numNodes nodes)"
	echo -e "\t- drop associated LVM volume group ($vgName) and all associated PV's"
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
		echo -e "\n\n\tRemoving configuration"
		resetCluster
	else
		echo -e "\n\nRun Aborted by user"
		return 8
	fi
	
}


echo -e "\nundodeploy.sh starting"
main "$@";
echo -e "\nundodeploy.sh finished - highest RC = $?"
