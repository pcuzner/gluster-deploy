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
#  ###############################################################
#  # NB. This script MUST run as root to be able to detect btrfs #
#  #     filesystems properly                                    #
#  ###############################################################

import 	subprocess
import 	sys
import 	os

from optparse import OptionParser

def issueCMD(command):
	""" 
	issueCMD takes a command to issue to the host and returns the response as a list 
	NB. Should be replaced by python-sh, but python-sh is not in base pkgs for RHEL6
	or RHS2.x/RHS3.
	"""

	cmdWords = command.split()
	try:
		out = subprocess.Popen(cmdWords,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(response, errors)=out.communicate()					# Get the output...response is a byte
		rc = out.returncode
	except Exception:
		response = 'command not found\n'
		rc=12
	
	return (rc, response.split('\n')[:-1])		# use split to return a list,
												# and skip the last null element

def getDisks():
	"""
	use lsblk to determine a list of potentially usable empty drives
	"""
	disks = dict()
	
	if DEBUG:
		print "\nLooking for available and unused disks;"
	
	#
	# PKNAME would be useful, but this is not available in RHEL6	
	(rc, lsblkOutput) = issueCMD('lsblk -l -n -b -t -o NAME,ROTA,SIZE,TYPE')
	
	# Look at the output (skip last null list element) 
	for devStr in lsblkOutput:
		
		devInfo = devStr.split()
		diskName = devInfo[0]
		action = 'discarded'
		if devInfo[3] == 'disk':
			
			# we have a disk, but before we accept this as a candidate does
			# it have any child devices (LVM, partitions)
			(rc, depList) = issueCMD('lsblk -n -l /dev/%s'%(diskName))

			if len(depList) == 1:		# Just itself, we like these :)
				
				if not btrfsDevice(diskName):
					diskType = 'SSD' if devInfo[1] == 0 else 'HDD'
					sizeKB = int(devInfo[2]) / 1024
					disks[diskName] = {'disktype' : diskType, 'size' : sizeKB}
					action='ACCEPTED - %s is a %d KB, empty %s'%(diskName,sizeKB,diskType)
				else:
					action += ", is a btrfs device"
			else:
				action+=", has child devices"
		else:
			action += ", is an existing partition/LV"		

		if DEBUG:
			print "  %s ... %s"%(diskName.ljust(42), action)
			
	
	return disks

def btrfsDevice(disk):
	""" Check if the supplied device name is known to btrfs """
	
	response = False
	
	if os.path.exists('/usr/sbin/btrfs'):

		(rc, btrfsOut) = issueCMD('btrfs filesystem show /dev/' + disk)
		if rc == 0:
			response = True
	
	return response


def getRaid():
	""" Look for a raid card and if found, return the type """
	
	cmd = "lspci | grep -i raid"
	(rc, pciOutput) = issueCMD(cmd)

	if rc > 0:
		raidCard = "none"
	else:							# lspci has returned something
		pciInfo = pciOutput[0].lower()
		
		if 'smart' in pciInfo:
			raidCard = 'smartarray'
		elif 'lsi' in pciInfo:
			raidCard = 'lsi'
		elif 'adaptec' in pciInfo:
			raidCard = 'adaptec'
		else:
			raidCard = 'unknown'
		
	return raidCard
	

def getSysInfo():
	""" Extract system attributes to associate with this node """

	sysInfo = {}	# Declare a dict to use for the system information	
	
	sysInfo['kernel'] = '.'.join(os.uname()[2].split('.')[:3])
	sysInfo['thinp'] = 'yes' if os.path.exists('/usr/sbin/thin_check') else 'no'
	sysInfo['btrfs'] = 'yes' if os.path.exists('/usr/sbin/btrfs') else 'no'
	sysInfo['glustervers'] = os.listdir('/usr/lib64/glusterfs')[0]
	
	sysInfo['memsize'] = open('/proc/meminfo').readlines()[0].split()[1]
	sysInfo['cpucount'] = str(len([ p for p in open('/proc/cpuinfo').readlines() if p.startswith('processor')]))
	sysInfo['raidcard'] = getRaid()

	if os.path.exists('/etc/redhat-storage-release'):
		sysInfo['osversion'] = open('/etc/redhat-storage-release').readlines()[0].rstrip('\n')
	else:
		sysInfo['osversion'] = open('/etc/issue').readlines()[0].rstrip('\n')

	profileList = ['Not Available']
	
	if os.path.exists('/usr/bin/tuned-adm'):
		
		(rc, tunedOutput) = issueCMD('tuned-adm list')
		if rc == 0:
			profileList = [ profile.split(' ')[1] for profile in tunedOutput if profile.startswith('-')]
		else:
			pass

	# convert the list of profiles to a string
	profiles = ','.join(profileList)
	
	sysInfo['tunedprofiles'] = profiles
		
	
	return sysInfo 

def main():
	""" 
	Generate an xml string of all eligible devices, and write to stdout
	"""
	
	sysInfo = getSysInfo()
	
	freeDisks = getDisks()		# returns a dict - key is device name, each element is also
								# a dict of 'disktype' and 'size'
	
	if OUTPUTTYPE == 'xml':
		
		deviceInfo = "<data>" 
		deviceInfo += ( "<sysinfo kernel='" + sysInfo['kernel'] + "' dmthinp='" + sysInfo['thinp'] + "' btrfs='"
				+ sysInfo['btrfs'] + "' glustervers='" + sysInfo['glustervers'] + "' memsize='" + sysInfo['memsize']
				+ "' cpucount='" + sysInfo['cpucount'] + "' raidcard='" + sysInfo['raidcard'] 
			 	+ "' osversion='" + sysInfo['osversion'] + "' tunedprofiles='" + sysInfo['tunedprofiles'] + "' />" ) 
	
	
		for diskName in freeDisks:
			deviceInfo += ( "<disk device='" + diskName + "' sizeKB='" + str(freeDisks[diskName]['size'])
						+ "' diskType='" + freeDisks[diskName]['disktype'] 
						+ "' />" )
	
		deviceInfo += "</data>"
		
	else:
		# output type is txt so format the output in a more human readable form 
		# to aid testing and debug
		deviceInfo = "\nSystem Information\n"
		tunedList = sysInfo['tunedprofiles'].split(',')
		tunedString = '\n'.join(['\t\t'+profName for profName in tunedList])
		deviceInfo += ( "\tKernel         - " + sysInfo['kernel'] + "\n"
					+   "\tOS Release     - " + sysInfo['osversion'] + "\n"
					+   "\tInstalled RAM  - " + str(int(sysInfo['memsize'])/1024) + " MB\n"
					+   "\tCores/Threads  - " + sysInfo['cpucount'] + "\n"
					+   "\tRaid Card Info - " + sysInfo['raidcard'] + "\n"
					+	"\ttuned Profles  - \n"
					+	tunedString + "\n"
					+   "Capabilities:\n\tThin Provisioning - " + sysInfo['thinp'] + "\n"
					+   "\tbtrfs - " + sysInfo['btrfs'] + "\n"
					+   "\nGluster Version - " + sysInfo['glustervers'] + "\n\n"
					+   "Unused Device List\n"
					)
		
		for diskName in freeDisks:
			deviceInfo += "\t" + "%s(%s)".ljust(10)%(diskName, freeDisks[diskName]['disktype']) + " "*4 + "%d KB\n"%(freeDisks[diskName]['size'])
			
		deviceInfo += "\n"

	print deviceInfo

	return 

if __name__ == '__main__':
	
	usageInfo = "usage: %prog [options]"
	parser = OptionParser(usage=usageInfo,version="%prog 1.2")
	parser.add_option("-f","--format",dest="outputFormat",default="xml",type="choice",choices=['xml','txt'],help="Output format - xml (default) or txt")
	parser.add_option("-d","--debug",dest="debug",action="store_true", default=False, help="provide more debug info")

	(options, args) = parser.parse_args()
	
	DEBUG = options.debug
	OUTPUTTYPE = options.outputFormat

	if os.getuid() == 0:
		main()
	else:
		print "findDevs needs to be invoked as the root user\n"
		
