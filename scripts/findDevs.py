#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  findDevs.py
#  
#  Copyright 2013 Paul <paul@rhlaptop>
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

def issueCMD(command):
	""" issueCMD takes a command to issue to the host and returns the response
		as a list
	"""

	cmdWords = command.split()
	try:
		out = subprocess.Popen(cmdWords,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(response, errors)=out.communicate()					# Get the output...response is a byte
	except Exception:
		response = 'command not found\n'
															# string that includes \n
	
	return response.split('\n')								# use split to return a list

def filterDevices(partList):
	""" Take a list of devices from proc/partitions and retun only the disk devices """

	validDevs = ('sd', 'vd', 'hd')
	
	for partDetail in reversed(partList):
		(major, minor, blocks, device) = partDetail.split()
		if not device.startswith(validDevs):
			partList.remove(partDetail)
	
	return partList

def filterPartitions(partitions):
	
	disks = {}
	
	for partDetail in partitions:
		(major, minor, blocks, device) = partDetail.split()

		if device[-1].isdigit():
			num = filter(str.isdigit,device)
			disk = device.replace(num,'')
			if disks.has_key(disk):
				del disks[disk]
			continue
			
		disks[device] = blocks	
		
	pass
	return disks
	
def filterLVM(disks):
	
	pvsOut = issueCMD('pvs --noheading')
	for pvData in pvsOut:
		fullDevName = pvData.split()[0]
		diskName = fullDevName.replace('/dev/','')
		if disks.has_key[diskName]:
			del disks[diskName]
	return disks

def filterBTRFS(disks):
	toDelete =[]
	for disk in disks:
		btrfsOut = issueCMD('btrfs filesystem show /dev/' + disk)
		
		if 'command not found' in btrfsOut[0]:
			continue
		elif btrfsOut[0].startswith('Label'):
			toDelete.append(disk)
			
	for btrfsDisk in toDelete:
		del disks[btrfsDisk]
	
	return disks


def main():
	
	# get list of partitions on this host
	partList = issueCMD('cat /proc/partitions')[2:-1]			# take element 2 onwards

	partitions = filterDevices(partList)	# list
	disks = filterPartitions(partitions)	# dict
	unusedDisks = filterBTRFS(disks)

	retString = ''

	for disk in unusedDisks:
			sys.stdout.write(disk + " " + unusedDisks[disk] + "\n") 
			#retString = retString + disk + " " + unusedDisks[disk] + ","

	#retString = retString[:-1]	# remove the trailing ','

	# Using sys.stdout.write avoids the carriage return/newline info being passed back
	#sys.stdout.write(retString)

	return 

if __name__ == '__main__':
	main()

