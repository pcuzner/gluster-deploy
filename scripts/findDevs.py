#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  findDevs.py
#  
#  Copyright 2013 Paul Cuzner <paul.cuzner@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import subprocess
import sys
import os

DEBUG=False

def issueCMD(command):
	""" issueCMD takes a command to issue to the host and returns the response as a list """

	cmdWords = command.split()
	try:
		out = subprocess.Popen(cmdWords,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(response, errors)=out.communicate()					# Get the output...response is a byte
	except Exception:
		response = 'command not found\n'
	
	return (out.returncode, response.split('\n'))							# use split to return a list

def filterDisks(partList):
	""" Take a list of devices from proc/partitions and return only the disk devices """

	validDevs = ('sd', 'vd', 'hd')
	
	for partDetail in reversed(partList):
		(major, minor, blocks, device) = partDetail.split()
		if not device.startswith(validDevs):
			if DEBUG:
				print "filterDisks removing " + partDetail
			
			partList.remove(partDetail)
	
	return partList

def filterPartitions(partitions):
	""" 
	Look at the parition list (devices), and build a dict of unique device
	names that don't have paritions i.e. sda, but not sda1 or sda2 
	"""
		
	disks = {}
	
	for partDetail in partitions:
		(major, minor, blocks, device) = partDetail.split()

		if device[-1].isdigit():
			num = filter(str.isdigit,device)
			disk = device.replace(num,'')
			if disks.has_key(disk):
				
				if DEBUG:
					print "filterPartitions dropping " + disk
					
				del disks[disk]
				
			continue
			
		disks[device] = blocks	
		
	pass
	return disks
	
def filterLVM(disks):
	""" 
	Receive a list of potenial disks and compare them with existing disks (pv's)
	used by the LVM, filtering out any disk known to the LVM 
	"""
		
	(rc, pvsOut) = issueCMD('pvs --noheading')
	
	for pvData in pvsOut:
		if pvData:
		
			fullDevName = pvData.split()[0]
			diskName = fullDevName.replace('/dev/','')
			if diskName in disks:
				
				if DEBUG:
					print "filterLVM dropping " + diskName
					
				del disks[diskName]
				
	return disks

def filterBTRFS(disks):
	""" 
	Receive potential disks to use for gluster, and attempt to query btrfs to see
	if they are btrfs devices. If so, filter them out and return remaining devices
	to the caller 
	"""
	
	toDelete =[]
	for disk in disks:
		
		(rc, btrfsOut) = issueCMD('btrfs filesystem show /dev/' + disk)
		
		if 'command not found' in btrfsOut[0]:
			continue
		elif btrfsOut[0].startswith('Label'):
			toDelete.append(disk)
			
	for btrfsDisk in toDelete:
		if DEBUG:
			print "filterBTRFS dropping " + btrfsDisk
		del disks[btrfsDisk]
	
	return disks

def getRaid():
	""" Look for a raid card and if found, return the type """
	
	cmd = "lspci | grep -i raid"
	(rc, pciOutput) = issueCMD(cmd)

	if len(pciOutput) == 0:
		raidCard = "unknown"
	else:							# lspci has returned something
		pciInfo = pciOutput[0].lower()
		if pciInfo == '':			# if no raid is present we just get null
			raidCard = 'unknown'
		else:
			if 'smart' in pciInfo:
				raidCard = 'smartarray'
			elif 'lsi' in pciInfo:
				raidCard = 'lsi'
			elif 'adaptec' in pciInfo:
				raidcard = 'adaptec'
		
	return raidCard

def getSysInfo():
	""" Extract system attributes to associate with this node """
	
	
	kernel = '.'.join(os.uname()[2].split('.')[:2])
	thinp = 'yes' if os.path.exists('/usr/sbin/thin_check') else 'no'
	btrfs = 'yes' if os.path.exists('/usr/sbin/btrfs') else 'no'
	glusterVers = os.listdir('/usr/lib64/glusterfs')[0]
	
	memSize = open('/proc/meminfo').readlines()[0].split()[1]
	cpuCount = len([ p for p in open('/proc/cpuinfo').readlines() if p.startswith('processor')])
	raidCard = getRaid()

	
	sysinfo = ( "<sysinfo kernel='" + kernel + "' dmthinp='" + thinp + "' btrfs='"
				+ btrfs + "' glustervers='" + glusterVers + "' memsize='" + memSize
				+ "' cpucount='" + str(cpuCount) + "' raidcard='" + raidCard + "' />" ) 
	
	
	return sysinfo 
	

def main():
	""" 
	Invoke the filters to determine if there are any devices unused on the 
	current host. 
	
	NB. MUST be run as root 
	"""
	
	sysInfo = getSysInfo()
	
	# get list of partitions on this host
	(rc, partList) = issueCMD('cat /proc/partitions')		# take element 2 onwards

	devices = filterDisks(partList[2:-1])	# 1st two lines are headers, so ignore
	disks = filterPartitions(devices)		# dict
	noLVM = filterLVM(disks)
	unusedDisks = filterBTRFS(noLVM)
	
	xmlString = "<data>" + sysInfo

	for disk in unusedDisks:
		xmlString += "<disk device='" + disk + "' sizeKB='" + unusedDisks[disk] + "' />"

	xmlString += "</data>"

	print xmlString

	return 

if __name__ == '__main__':
	if len(sys.argv) > 1:
		if sys.argv[1].lower() == 'debug':
			DEBUG = True
	main()

