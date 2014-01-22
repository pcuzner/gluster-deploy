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

from optparse import OptionParser

def issueCMD(command):
	""" issueCMD takes a command to issue to the host and returns the response as a list """

	cmdWords = command.split()
	try:
		out = subprocess.Popen(cmdWords,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(response, errors)=out.communicate()					# Get the output...response is a byte
		rc = out.returncode
	except Exception:
		response = 'command not found\n'
		rc=12
	
	return (rc, response.split('\n'))							# use split to return a list

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

	sysInfo = {}	# Declare a dict to use for the system information	
	
	sysInfo['kernel'] = '.'.join(os.uname()[2].split('.')[:2])
	sysInfo['thinp'] = 'yes' if os.path.exists('/usr/sbin/thin_check') else 'no'
	sysInfo['btrfs'] = 'yes' if os.path.exists('/usr/sbin/btrfs') else 'no'
	sysInfo['glustervers'] = os.listdir('/usr/lib64/glusterfs')[0]
	
	sysInfo['memsize'] = open('/proc/meminfo').readlines()[0].split()[1]
	sysInfo['cpucount'] = str(len([ p for p in open('/proc/cpuinfo').readlines() if p.startswith('processor')]))
	sysInfo['raidcard'] = getRaid()
	
	return sysInfo 

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
	
	if OUTPUTTYPE == 'xml':
		
		deviceInfo = "<data>" 
		deviceInfo += ( "<sysinfo kernel='" + sysInfo['kernel'] + "' dmthinp='" + sysInfo['thinp'] + "' btrfs='"
				+ sysInfo['btrfs'] + "' glustervers='" + sysInfo['glustervers'] + "' memsize='" + sysInfo['memsize']
				+ "' cpucount='" + sysInfo['cpucount'] + "' raidcard='" + sysInfo['raidcard'] + "' />" ) 
	
	
		for disk in unusedDisks:
			deviceInfo += "<disk device='" + disk + "' sizeKB='" + unusedDisks[disk] + "' />"
	
		deviceInfo += "</data>"
		
	else:
		# output type is txt so format the output in a more human readable form 
		# to aid testing and debug
		deviceInfo = "\nSystem Information\n"
		deviceInfo += ( "\tKernel         - " + sysInfo['kernel'] + " series\n"
					+   "\tInstalled RAM  - " + str(int(sysInfo['memsize'])/1024) + " MB\n"
					+   "\tCores/Threads  - " + sysInfo['cpucount'] + "\n"
					+   "\tRaid Card Info - " + sysInfo['raidcard'] + "\n\n"
					+   "Capabilities:\n\tThin Provisioning - " + sysInfo['thinp'] + "\n"
					+   "\tbtrfs - " + sysInfo['btrfs'] + "\n"
					+   "\nGluster Version - " + sysInfo['glustervers'] + "\n\n"
					+   "Unused Device List\n"
					)
		for disk in unusedDisks:
			deviceInfo += "\t" + disk.ljust(6) + " "*4 + unusedDisks[disk] + " KB\n"
			
		deviceInfo += "\n"

	print deviceInfo

	return 

if __name__ == '__main__':
	
	usageInfo = "usage: %prog [options]"
	parser = OptionParser(usage=usageInfo,version="%prog 1.1")
	parser.add_option("-f","--format",dest="outputFormat",default="xml",type="choice",choices=['xml','txt'],help="Output format - xml (default) or txt")
	parser.add_option("-d","--debug",dest="debug",action="store_true", default=False, help="provide more debug info")

	(options, args) = parser.parse_args()
	
	DEBUG = options.debug
	OUTPUTTYPE = options.outputFormat

	main()

