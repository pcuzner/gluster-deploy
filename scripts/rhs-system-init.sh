#!/bin/bash
# Title : rhs-system-init.sh
# Author : Veda Shankar
# Description : 
# RHS system initialization script.  The script is supposed to be run after
# ISO installtion and setting up the network.  
# The script does the following:
#     - Identify the RAID volume using the WWID and create a brick.
#     - Based on the use case, run the corresponding performance tuning profile.
#     - Register with RHN and subscribe to correct software channels.
#     - Run yum update to apply the latest updates.
#
# History:
# 12/13/2012 Veda Shankar  Created
# 12/20/2012 Veda : Check the correct RHN channels before applying updates
# 01/18/2013 Veda : Incorporate recommended options for pv create, mkfs and 
#                   mounting.
# 01/24/2013 Veda : Provide -n option for dry-run.

# Default settings
ME=$(basename $0);
dryrun=0
logfile=/root/rhs-init.log
vgname_base=RHS_vg
lvname_base=RHS_lv
brickpath=/rhs
workload=general
inode_size=512
tune_profile=rhs-high-throughput

# LVM settings best suited for the standard RHS deployment 
# which has 12 drives in RAID6 configuration with 256-KB stripe size.
stripesize=256k
stripe_elements=10
dataalign=2560k
fs_block_size=8192

exec > >(tee /root/rhs-init.log)
exec 2>&1

function usage {
    cat <<EOF
Usage:  $ME [-h] [-u virtual|object]

General:
  -u <workload>   virtual - RHS is used for storing virtual machine images.
                  object  - Object Access (HTTP) is the primary method to 
                            access the RHS volume.
                  The workload helps decide what performance tuning profile 
                  to apply and other customizations.  
                  By default, the  general purpose workload is assumed.

  -n              Dry run to show what devices will be used for brick creation.
  -h              Display this help.

EOF
    exit 1
}


function quit {
    exit $1
}

function yesno {
   while true; do
       read -p "$1 " yn
       case $yn in
           [Yy]* ) return 0;;
           [Nn]* ) return 1;;
           * ) echo "Please answer yes or no.";;
       esac
   done
}


function create_pv {
    dev=$1
    size=$2
    if [ ! -h /dev/mapper/$dev ]
    then
       echo "/dev/mapper/$dev - Not Present!"
       return 1
    fi
    echo "Create Physical Volume with device $dev of size $size."
    [ $dryrun -eq 1 ] && return 0
    
    pvcreate --dataalignment $dataalign /dev/mapper/$dev
    return  $?
}

function create_vg {
    dev=$1
    vgname=$2
    echo "Create Volume Group $vgname."
    [ $dryrun -eq 1 ] && return 0
    
    vgcreate $vgname /dev/mapper/$dev
    return  $?
}

function create_lv {
    vgname=$1
    lvname=$2
    echo "Create Logical Volume $lvname."
    [ $dryrun -eq 1 ] && return 0
    
    lvcreate -l 85%FREE -n $lvname $vgname
    return  $?
}

function create_fs {
    vgname=$1
    lvname=$2
    echo "Create XFS file system /dev/$vgname/$lvname."
    echo "mkfs.xfs -i size=$inode_size -n size=$fs_block_size -d su=$stripesize,sw=$stripe_elements /dev/$vgname/$lvname" 
    [ $dryrun -eq 1 ] && return 0
    
    mkfs.xfs -i size=$inode_size -n size=$fs_block_size -d su=$stripesize,sw=$stripe_elements /dev/$vgname/$lvname 
    return  $?
}

function create_fstab_entry {
    [ $dryrun -eq 1 ] && return 0
    vgname=$1
    lvname=$2
    mount=$3
    uuid=`xfs_admin -u /dev/$vgname/$lvname | cut -f3 -d " "`
    echo $uuid
    grep -wq $uuid /etc/fstab > /dev/null 2>&1 && return 1
    echo "Create fstab entry for /dev/mapper/$vgname-$lvname ($uuid)."
    echo "UUID=$uuid $mount xfs \
          allocsize=4096,nobarrier,inode64,logbsize=256K,logbufs=8 \
          1 2" >> /etc/fstab
    return 0
}

function create_bricks {
    
    declare -a devmapper_name=(`multipath -l | grep 'dm-' | cut -f1 -d" "`)
    declare -a devmapper_size=(`multipath -l | grep "size=" | \
                                cut -f2 -d "=" | cut -f1 -d" "`)
    
    count=0
    dev_count=1
    for dev in "${devmapper_name[@]}"
    do
       # Check for boot raid volume
       pvdisplay | grep -wq  /dev/mapper/$dev 
       ret=$?
       if [ $ret -eq 0 ]
       then
           (( count++ ))
           continue
       fi

       echo "---- Device# ${dev_count} ----"
       vgname=$vgname_base$dev_count 
       lvname=$lvname_base$dev_count

       # Create Physical Volume
       create_pv $dev ${devmapper_size[$count]} || exit 1
    
       # Create Volume Group
       create_vg $dev $vgname || exit 1
    
       # Create Logical Group
       create_lv $vgname $lvname || exit 1

       # Create XFS file system
       create_fs $vgname $lvname || exit 1

       # Make directory for brick mount point
       [ $dryrun -eq 0 ] && mkdir -p $brickpath/brick$dev_count

       # Create entry in /etc/fstab
       create_fstab_entry $vgname $lvname $brickpath/brick$dev_count || exit 1
    
       # Mount all the bricks.
       [ $dryrun -eq 0 ] && mount -a
    
       (( count++ ))
       (( dev_count++ ))
            echo
    done
}


function tune_performance {

    echo "---- Performance tune for $workload storage ----"
    tuned-adm profile $tune_profile
}


function channels_error {
   declare -a reg_channels=(`rhn-channel --list`)
   echo "ERROR: All required channels are not registered!"
   echo -e "Required Channels:\n\trhel-x86_64-server-6.2.z\n\trhel-x86_64-server-sfs-6.2.z\n\trhel-x86_64-server-6-rhs-2.0"
   echo -e "Registered Channels:"
   for chan in "${reg_channels[@]}"
   do
         echo -e "\t$chan"
   done
   return 1
}


function check_channels {

   declare -a reg_channels=(`rhn-channel --list`)
   if [ ${#reg_channels[@]} -lt 3 ]
   then
      channels_error
      return 1
   fi

   correct=0
   for chan in "${reg_channels[@]}"
   do
      if [ "$chan" == "rhel-x86_64-server-6.2.z" \
           -o "$chan" == "rhel-x86_64-server-sfs-6.2.z" \
           -o "$chan" == "rhel-x86_64-server-6-rhs-2.0" \
         ]
      then
         (( correct++ ))
      fi
   done

   if [ $correct -ne 3 ]
   then
      channels_error
      return 1
   fi

   echo -e "Registered Channels:"
   for chan in "${reg_channels[@]}"
   do
         echo -e "\t$chan"
   done
   return 0
}


function rhn_register_update {

    profile_name=`hostname -s`
    profile_name=RHS_$profile_name
    rhn_register

    echo "---- Register Channels ----"
    read -p "RHN Login: " rhn_login
    read -s -p "RHN Password: " rhn_password
    echo ""
    rhn-channel --verbose --user $rhn_login --password $rhn_password \
        --add --channel=rhel-x86_64-server-sfs-6.2.z
    rhn-channel --verbose --user $rhn_login --password $rhn_password \
        --add --channel=rhel-x86_64-server-6-rhs-2.0

    check_channels || return 1
    echo "System registered to the correct Red Hat Channels!"
    if yesno "Do you want to apply updates now? "
    then
        echo "---- Apply Updates ----"
        yum -y update
    fi
}


function main {
    
    while getopts ":nhu:" OPT; do
    case "$OPT" in
        u)
            case $OPTARG in
                object)
                    workload=$OPTARG
                    inode_size=1024
                    ;;
                virtual)
                    workload=$OPTARG
                    # Future
                    # tune_profile=rhs-virtualstore-support
                    ;;
                *)
                    echo "Unrecognized option."
                    usage # print usage and exit
            esac
            ;;
        n)
	    dryrun=1
            ;;
        h)
	    usage # print usage and exit
            ;;
        \?)
            echo "Invalid option: -$OPTARG"
	    usage # print usage and exit
            ;;
        :)
            echo "Option -$OPTARG requires an argument."
            usage # print usage and exit
            ;;
    esac
    done
    echo "Setting workload to $workload."
    create_bricks
    [ $dryrun -eq 1 ] && return 0
    tune_performance
    rhn_register_update
}

# Call Main
main "$@";


