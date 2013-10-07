#!/bin/bash

# formatBrick.sh
# Based on code created by Veda Shankar at Red Hat
#
# Return Codes
# 0  .. All good
# 4  .. dry run only - no action taken
# ?  .. lvm command returned a non-zero value, execution aborted
#
# Future Changes
# 1. attempt to look for raid tools to get the stripe/chunk size and stripe width for xfs 
#    format - smartarray, lsi commands?
#

LVPREFIX='gluster'
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
	local checkvg=$(vgs | grep "$vgName")
	
	if [ -z "$checkvg" ] ; then 
		action="vgcreate"
		vgcreate $vgName /dev/$devID
		rc=$?
	else
		action="vgextend"
		vgextend $vgName /dev/$devID
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

	local lv=$1
	local devID=$2
	local volGroup=$3
	local snapSpace=$4
	local alloc=100
	let alloc=alloc-$snapSpace

	logger "formatBrick.sh creating lv $lv in VG $volGroup using $alloc % of $devID"
	[ $dryrun -eq 1 ] && return 4
	
	# create an lv allocated to this device, using the snapreserve to control
	# freespace to leave on the pv
	lvcreate  -n $lv -l $alloc%PVS $volGroup /dev/$devID
	rc=$?
	
	if [ $rc -eq 0 ] ; then 
		logger "formatBrick.sh lvcreate for $lvname successful"
	else
		logger "formatBrick.sh lvcreate failed RC $rc"
	fi
	
	return $rc

}

function create_filesystem {
	local volGroup=$1
	local lv=$2
	local inodeSize=$3
	local rc=0
	
	logger "formatBrick.sh creating filesystem on lv $lv"
	[ $dryrun -eq 1 ] && return 4
	
	# run mkfs.xfs with an inode, and imaxpct of 25
	mkfs.xfs -i size=$inodeSize -n size=$FSBLOCKSIZE  /dev/$volGroup/$lv 
	rc=$?
	
	if [ $rc -eq 0 ] ; then 
		logger "formatBrick.sh filesystem on lv $lvName created successfully"
	else
		logger "formatBrick.sh mkfs.xfs failed on $lvName - RC $rc"
	fi
		
	return $rc
		
}

function update_fstab {
	local volGroup=$1
	local lv=$2
	local mountPoint=$3
	local rc=0
	
	local uuid=$(blkid /dev/$volGroup/$lv | cut -f2 -d'"')
	grep -wq $uuid /etc/fstab 
	if [ $? -eq 0 ] ; then 
		logger "formatBrick.sh update of /etc/fstab skipped - entry already there"
		return 1
	else
		logger "formatBrick.sh will update /etc/fstab"
		mkdir -p $mountPoint
		echo "UUID=$uuid $mountPoint xfs \
          defaults,allocsize=4096,inode64,logbsize=256K,logbufs=8,noatime \
          0 2" >> /etc/fstab
		rc=$?
		
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
	
	# create pv
	create_pv $devID  || return $?

	# create/extend vg
	create_vg $vgName $devID || return $?
	
	# create lv
	lvName="$LVPREFIX-$devID"
	create_lv $lvName $devID $vgName $snapReserve || return $?
	
	# make filesystem
	create_filesystem $vgName $lvName $inodeSize || return $?
	
	# update fstab
	update_fstab $vgName $lvName $mountPoint  || return $?
	
	# mount it
	mount_filesystem || return $?

}


function main {
	
	local rc=0
	dryrun=0
	
    while getopts ":tw:s:v:m:d:" OPT; do
	    case "$OPT" in
			t)
				dryrun=1
				;;
			d)
				devID=$OPTARG
				;;
			s)	
				snapReserve=$OPTARG
				;;
			v)	
				vgName=$OPTARG
				;;
			m)
				mountPoint=$OPTARG
				;;
	        w)
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

