#!/bin/bash
#
# Script used during testing to tear down configs.
#
# WARNING this is not complete, and is only intended to help
# improve the test cycle time
#

echo "Dropping the gluster configuration"

# Get a list of gluster volumes
# Loop through each volume name
# 	issue a stop
#	issue a delete



echo "processing remote nodes"
echo -e "\tUnmounting filesystems"
for i in 2 3 4 ; do
  ssh rhs1-$i umount /gluster/brick1
done

echo -e "\tDropping lv and vg"
for i in 2 3 4; do 
  ssh rhs1-$i vgremove glustervg -f
done

echo -e "\tdropping the pv"
for i in 2 3 4; do
  ssh rhs1-$i pvremove /dev/vdb
done

echo -e "\tremoving the brick entry from remote fstab's"
for i in 2 3 4; do 
  ssh rhs1-$i /bin/cp -f /etc/fstab /etc/fstab_saved
  ssh rhs1-$i 'sed -n -i "/gluster\/brick1/!p" /etc/fstab' 
  ssh rhs1-$i 'rm -fr /gluster'
done 

echo "processing local node"
umount /gluster/brick1
vgremove glustervg -f
pvremove /dev/vdb
echo -e "\tBacking up local fstab"
/bin/cp -f /etc/fstab /etc/fstab_saved
echo -e "\tRemoving brick entry from fstab"
sed -n -i '/gluster\/brick1/!p' /etc/fstab
echo -e "\tRemoving /gluster dir root"
rm -fr /gluster
