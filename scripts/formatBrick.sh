#!/bin/bash

# formatBrick.sh
# Based on code created by Veda Shankar at Red Hat
#
# Return Codes
# 0  .. All good
# 4  .. dry run only - no action taken
# ?  .. lvm command returned a non-zero value, execution aborted
#
# Change History
# ../11/2013 Updated to support dm-thinp snapshots
# ../10/2013 Created
#
# Future Changes
# 1. attempt to look for raid tools to get the stripe/chunk size and stripe width for xfs 
#    format - smartarray, lsi commands?
# 

FSBLOCKSIZE=8192

function create_pv {
	local devID=$1
	
	# Future - use dataalignment based on whether the disk is a raid lun?
	# could detect this in the findDisks.py code, and update the disk object 
	# with an attribute that we can use in formatBrick.sh
	logger "formatBrick.sh running pvcreate for device $devID"
	
	[ $dryrun -eq 1 ] && return 4
	
	pvcreate  /dev/$devID
	local rc=$?
	
	if [ $rc -eq 0 ] ; then 
		logger "formatBrick.sh pvcreate completed OK on device $devID"
	else
		logger "formatBrick.sh pvcreate failed with RC $rc on device $devID"
	fi
	
	return $rc
}

function create_vg {
	local vgName=$1
	local devID=$2
	local action=""
	local rc=0
	
	# check if vg already exists - if not create it
	# if so extend the vg with this device
	local checkvg=$(vgs $vgName)
	
	if [ $checkvg -eq 0 ] ; then 
		action="vgextend"
		vgextend $vgName /dev/$devID
		rc=$?
	else
		action="vgcreate"
		vgcreate $vgName /dev/$devID
		rc=$?
	fi	
	
	if [ $rc -eq 0 ] ; then 
		logger "formatBrick.sh $action for volume group $vgName with device $devID completed OK"
	else
		logger "formatBrick.sh $action for volume group $vgName with device $devID failed with RC $rc"	
	fi
		
	return $rc
}

function create_lv {
	
	#local lv=$1
	local devID=$1
	local lvSize=$2

	if [ $snapRequired == "YES" ] ; then 
		local lvType='THIN'
	else
		local lvType='THICK'
	fi

	logger "formatBrick.sh creating '$lvType' lv $lv in VG $volGroup using /dev/$devID"
	[ $dryrun -eq 1 ] && return 4

	if [ $snapRequired == "YES" ]; then 
		# need to allocate the thinpool then the thindev
		local poolName=$vgName"pool"
		local poolSize=$(pvdisplay /dev/$devID | awk '/Total PE/ { print $3;}')
		let poolSize=$((poolSize - 3))
		lvcreate -l $poolSize -T $vgName/$poolName
		rc=$?
		if [ $rc -eq 0 ]; then 
			# Allocate the thindev
			lvcreate -V $lvSize -T $vgName/$poolName -n $lvName
			rc=$?
		fi
			
	else
		# only need to allocate a standard lv
		lvcreate  -n $lvName -l 100%PVS $vgName /dev/$devID
		rc=$?
	fi
	
	if [ $rc -eq 0 ] ; then 
		logger "formatBrick.sh lvcreate for $lvname successful"
	else
		logger "formatBrick.sh lvcreate failed RC $rc"
	fi
	
	return $rc

}

# function get_next_lv {
#	local lvTarget=$1
#
#	local lastLV=$(lvs | grep $lvTarget | tail -n 1 | awk '{print $1}')
#	if [ -z $lastLV ]; then 
#		# lastLV is empty, so there are no previous volumes of this name
#		local newSuffix='00'
#	else
#		# A volume of this name pre-exists, so lets look at it to create new suffix
#		local seq=$(echo $lastlv | awk ' {print substr($0,length($0)-1,2)}')
#		let seq=seq+1
#		local newSuffix=$(printf "%02d" $seq)
#	fi
#
#
#	return $newSuffix
#}


function create_filesystem {

	local inodeSize=$1
	local rc=0
	
	logger "formatBrick.sh creating filesystem on lv $lv"
	[ $dryrun -eq 1 ] && return 4
	
	# run mkfs.xfs with an inode, and imaxpct of 25
	mkfs.xfs -i size=$inodeSize -n size=$FSBLOCKSIZE  /dev/$vgName/$lvName 
	rc=$?
	
	if [ $rc -eq 0 ] ; then 
		logger "formatBrick.sh filesystem on lv $lvName created successfully"
	else
		logger "formatBrick.sh mkfs.xfs failed on $lvName - RC $rc"
	fi
		
	return $rc
		
}

function update_fstab {
	
	local devPath=$1
	local rc=0
	
	local uuid=$(blkid $devPath | cut -f2 -d'"')
	grep -wq $uuid /etc/fstab 
	if [ $? -eq 0 ] ; then 
		logger "formatBrick.sh update of /etc/fstab skipped - entry already there"
		return 1
	else
		logger "formatBrick.sh will update /etc/fstab"
		mkdir -p $mountPoint
		
		if [ $brickType == "LVM" ]; then 
			echo "UUID=$uuid $mountPoint xfs "\
			  "defaults,allocsize=4096,inode64,logbsize=256K,logbufs=8,noatime "\
			  "0 2" >> /etc/fstab
			rc=$?
		else
			echo "UUID=$uuid $mountPoint btrfs defaults 0 0" >> /etc/fstab
			rc=$?
		fi
		
		if [ $rc -eq 0 ]; then
			logger "formatBrick.sh updated fstab successfully"
		else
			logger "formatBrick.sh failed to update fstab"
		fi
	fi

	
	return $rc
}

function mount_filesystem {
	local rc=0
	mount -a
	rc=$?
	return $rc
}

function create_brick {
	
	local devPath
	echo $brickType
	
	if [ $brickType == "LVM" ]; then 

		# LVM Processing Steps
		create_pv $devID  || return $?

		create_vg $vgName $devID || return $?

		create_lv $devID $lvSize || return $?

		# make filesystem
		create_filesystem $inodeSize || return $?

		devPath="/dev/$vgName/$lvName"

	elif [ $brickType == "BTRFS" ]; then
		# Insert btrfs function calls in here
		
		devPath="/dev/$devID"
		:
	else
		logger "formatBrick.sh was passed an unknown brick type - run aborted"
		return 16
	fi

	
	
	# update fstab
	update_fstab $devPath  || return $?
	
	# mount it
	mount_filesystem || return $?

}


function dump_parms {

	logger "formatBrick.sh invoked as follows;"
	logger "dryrun :$dryrun"
	logger "devID : $devID"
	logger "brickType : $brickType"
	logger "snapReqd : $snapRequired"
	logger "lvsize: $lsSize"
	logger "lvName : $lvName"
	logger "vgName : $vgName"
	logger "mount : $mountPoint"
	logger "workload : $workload"
	logger "inodesz : $inodeSize"

}




function main {
	
	local rc=0
	dryrun=0
	
	while getopts "tDu:c:s:l:b:v:m:n:d:" OPT; do
		case "$OPT" in
			t)
				dryrun=1
				;;
			D)
				dump_parms
				;;
			d)
				devID=$OPTARG
				;;
			b)
				brickType=$OPTARG
				;;
			c)
				raidCard=$OPTARG
				;;
			s)
				snapRequired=$OPTARG
				;;
			l)	
				lvSize=$OPTARG
				;;
			n)	
				lvName=$OPTARG
				;;				
			v)	
				vgName=$OPTARG
				;;
			m)
				mountPoint=$OPTARG
				;;
			u)
				case $OPTARG in
				
					object)
						workload=$OPTARG
						inodeSize=1024
						;;
					virtual)
						workload=$OPTARG
						inodeSize=512
						
						;;
					*)
						workload='generic'
						inodeSize=512
				;;
				esac
				;;
			:)
				echo "Option -$OPTARG requires an argument."
				;;
		esac
	done
	

	
	logger "formatBrick.sh processing started"
	
	create_brick $devID 
	rc=$?
	
	logger "formatBrick.sh processing finished - RC=$rc"
	exit $rc
	
}

main "$@";

