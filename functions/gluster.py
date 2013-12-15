#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  gluster.py
#  
#  Copyright 2013 Paul Cuzner <paul.cuzner@redhat.com>
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

from syscalls import issueCMD, SSHsession
import xml.etree.ElementTree as ETree

import globalvars as g

import logging
import time
import os


def parseOutput(outXML, elementType):
	"""	Receive the output of a command in xml format, and search for 
		elements that match the required type. Once found return them
		to the caller """
	pass
	return

def clusterMembers():
	"""	return a list of the members in a cluster using the output of
		pool list
	"""
	return issueCMD('gluster pool list')
	
def createVolume(xmlDoc):
	"""	function to define a gluster volume given an xml volume definition """
	
	cmdQueue = []
	bricks = []	
	#xmlRoot = ETree.fromstring(xmlString)

	
	
	# Volume parameters
	volumeDefinition = xmlDoc.find('volume')
	volName = volumeDefinition.attrib['name']
	volType = volumeDefinition.attrib['type']
	useCase = volumeDefinition.attrib['usecase']
	replicaParm = ' ' if ( volumeDefinition.attrib['replica'] == 'none') else (' replica ' + volumeDefinition.attrib['replica'])
	
	# protocols
	NFSstate  = 'nfs.disable off'  if ( xmlDoc.find('./volume/protocols').attrib['nfs'] == 'true' )  else 'nfs.disable on'
	CIFSstate = 'user.cifs enable' if ( xmlDoc.find('./volume/protocols').attrib['cifs'] == 'true' ) else 'user.cifs disable'
	
	# bricks
	for child in xmlDoc.findall('./volume/bricklist/brick'):
		bricks.append(child.attrib['fullpath'])
	numBricks = len(bricks)		# may want to check the number of bricks later...?
				
	# create volume syntax
	createCMD = "gluster vol create " + volName + replicaParm + " transport tcp "
	for brick in bricks:
		createCMD += brick + " "
	
	createCMD += " force"		# added to allow the root of the brick to be used (glusterfs 3.4)
	
	cmdQueue.append(createCMD)
	
	# Post Processing Options
	cmdQueue.append('gluster vol set ' + volName + ' ' + NFSstate)
	cmdQueue.append('gluster vol set ' + volName + ' ' + CIFSstate)
	
	if useCase.lower() == 'hadoop':
		# Added based on work done by Jeff Vance @ Red Hat
		cmdQueue.append('gluster vol set ' + volName + ' quick-read off')
		cmdQueue.append('gluster vol set ' + volName + ' cluster.eager-lock on')
		cmdQueue.append('gluster vol set ' + volName + ' performance.stat-prefetch off')
		pass
		
	elif useCase.lower() == 'virtualisation':
		
		# look to see what type of virt target it is
		target = xmlDoc.find('./volume/tuning').attrib['target']
		if target == 'glance':
			cmdQueue.append('gluster vol set ' + volName + ' storage.owner-gid 161')
			cmdQueue.append('gluster vol set ' + volName + ' storage.owner-uid 161')
			pass
		elif target == 'cinder':
			cmdQueue.append('gluster vol set ' + volName + ' storage.owner-gid 165')
			cmdQueue.append('gluster vol set ' + volName + ' storage.owner-uid 165')
			pass
		elif 'rhev' in target.lower():
			cmdQueue.append('gluster vol set ' + volName + ' storage.owner-gid 36')
			cmdQueue.append('gluster vol set ' + volName + ' storage.owner-uid 36')				
		
		if ('rhev' in target.lower()) or (target == 'cinder'):
			
			# Is the virt group available to use
			if os.path.isfile('/var/lib/glusterd/groups/virt'):
				cmdQueue.append('gluster vol set ' + volName + ' group virt')
				pass
			else:
				# Fallback settings if local virt group definition is not there
				cmdQueue.append('gluster vol set ' + volName + ' quick-read  off')
				cmdQueue.append('gluster vol set ' + volName + ' read-ahead  off')
				cmdQueue.append('gluster vol set ' + volName + ' io-cache  off')
				cmdQueue.append('gluster vol set ' + volName + ' stat-prefetch  off')
				cmdQueue.append('gluster vol set ' + volName + ' eager-lock enable')
				cmdQueue.append('gluster vol set ' + volName + ' remote-dio enable')
				pass
			
		
	# Add volume start to the command sequence
	cmdQueue.append('gluster vol start ' + volName)

	# log the number of commands that will be run
	numCmds = len(cmdQueue)
	g.LOGGER.debug("%s Creating volume %s - %d steps", time.asctime(), volName, numCmds)
	
	# Process the command sequence	
	retCode = 0
	stepNum = 1
	for cmd in cmdQueue:
		
		cmdType = ' '.join(cmd.split()[1:3]) + ' ...'
		g.MSGSTACK.pushMsg("Step %d/%d starting (%s)" %(stepNum, numCmds,cmdType))
		
		(rc, cmdOutput) = issueCMD(cmd)
		
		if rc == 0:	# retcode is 1st element, so check it's 0
						
			# push this cmd to the queue for reporting in the UI
			g.MSGSTACK.pushMsg("Step %d/%d completed" %(stepNum, numCmds))
			
			# Log the cmd being run as successful
			g.LOGGER.info("%s step %d/%d successful", time.asctime(), stepNum, numCmds)
			g.LOGGER.debug("%s Command successful : %s", time.asctime(), cmd)
			
		else:
			g.LOGGER.info("%s vol create step failed", time.asctime())
			
			g.LOGGER.debug("%s command failure - %s", time.asctime(), cmd)
			
			g.MSGSTACK.pushMsg("Step %d/%d failed - sequence aborted" %(stepNum, numCmds))
			
			# problem executing the command, log the response and return
			retCode = 8
			break
			
		stepNum +=1

	
	
	return retCode

def healthCheck():
	pass
		

def getPeers():
	"""	Run peer status to get a list of peers on the current server """
	pass
	return
	

class GlusterDisk:
	def __init__(self,nodeName,deviceID, size,formatRequired=False):
		self.nodeName = nodeName
		self.deviceID = deviceID
		self.sizeMB = size
		self.formatRequired = formatRequired
		self.formatComplete = False			# deprecated
		self.formatStatus = 'pending'		# pending -> complete || failed
		self.mountPoint = ""
		self.snapRequired = 'NO'
		self.thinSize = 0
		self.poolSize = 0
		self.useCase = ""
		self.vgName = ""
		self.lvName = ""
		self.localDisk = False
		self.brickType = 'LVM'
		
	def formatBrick(self,userPassword,raidCard):
		"""	Pass the node the format script for this brick """
		
		g.LOGGER.info('%s formatting %s as a brick on %s', time.asctime(), self.deviceID, self.nodeName )

		scriptPath = os.path.join(g.PGMROOT,'scripts/formatBrick.sh')
		scriptParms = ( " -D -d %s -c %s -b %s -v %s -s %s -l %s -p %s -m %s -u %s -n %s " % 
						(self.deviceID, 
						raidCard, 
						self.brickType, 
						self.vgName, 
						self.snapRequired, 
						str(self.thinSize), 
						str(self.poolSize),
						self.mountPoint, 
						self.useCase,
						self.lvName) )
						
		scriptName = scriptPath + scriptParms
		
		g.LOGGER.debug('%s Script invocation: %s', time.asctime(),scriptName)

		g.MSGSTACK.pushMsg("%s format on %s starting" %(self.deviceID, self.nodeName))

		if self.localDisk:
			(rc, resp) = issueCMD(scriptName)
			self.formatStatus = 'complete' if (rc == 0) else 'failed'

		else:
			
			ssh=SSHsession('root',self.nodeName,userPassword)
			(rc, resp) = ssh.sshScript(scriptName)
			
			self.formatStatus = 'complete' if (rc == 0) else 'failed'
		
		g.MSGSTACK.pushMsg("%s format on %s ended, RC=%d" %(self.deviceID, self.nodeName, rc))
		
		g.LOGGER.debug('%s formatBrick complete on %s with retcode = %s', time.asctime(), self.nodeName, str(rc))
		
		return 			

class GlusterNode:
	def __init__(self, nodeName):
		self.nodeName = nodeName
		self.userName = 'root'
		self.localNode = False
		self.userPassword = ''
		self.inCluster = False
		self.hasKey = False
		self.diskScanned = False
		self.brickCreated = False			# not needed?
		self.diskList = {}
		self.raidCard=''
		self.kernelVersion = ''
		self.dmthinp = False
		self.btrfs = False
		self.glusterVersion = ''
		self.memGB = 0
		self.cpuCount = 0
		
		
	def pushKey(self):
		""" push the local machines root account ssh key to this node """
		
		#(nodeName, nodePassword) = nodeData.split('*')
		
		#keyState.targetList.remove(nodeName)
		
		sshTarget = SSHsession(self.userName, self.nodeName, self.userPassword)
		copyRC = sshTarget.sshCopyID()
		
		if copyRC <= 4:
			#keyState.successList.append(nodeName)
			g.LOGGER.info('%s ssh key added successfully to %s', time.asctime(), self.nodeName)
			self.hasKey = True
		else:
			#keyState.failureList.append(nodeName)
			g.LOGGER.info('%s Adding ssh key to %s failed', time.asctime(), self.nodeName)
			self.hasKey = False
			
		
	def joinCluster(self):
		"""	run peer probe against this node """
		
		(rc, probeOutput) = issueCMD("gluster peer probe " + self.nodeName)
		
		if rc > 0:
			# update the clusterState properties
			g.LOGGER.debug("%s peer probe for %s failed", time.asctime(), self.nodeName)
			#clusterState.failureList.append(thisNode)
			self.inCluster = False
		else:
			# update the clusterState properties
			g.LOGGER.debug("%s peer probe for %s succeeded", time.asctime(), self.nodeName)
			#clusterState.successList.append(thisNode)
			self.inCluster = True
		pass
		
	def findDisks(self):
		"""	pass a scan script to the node, returning a list of unused disks in xml format """

		g.LOGGER.debug('%s getDisks scanning %s', time.asctime(), self.nodeName)
		
		scriptName = os.path.join(g.PGMROOT,'scripts/findDevs.py')
		
		g.LOGGER.debug('%s getDisks using script from %s', time.asctime(), scriptName)

		# check if this is the local node, if so, use issueCMD not ssh
		if self.localNode:
			(rc, diskOut) =  issueCMD(scriptName)
		else:
			sshTarget = SSHsession(self.userName, self.nodeName, self.userPassword)
			(rc, diskOut) = sshTarget.sshPython(scriptName)
		
		self.diskScanned = True

		if ( rc == 0 ):
			
			diskData = str(diskOut[0])
			xmlDoc = ETree.fromstring(diskData)
			freeDisks = xmlDoc.findall('disk')
			sysInfo = xmlDoc.find('sysinfo')
			
			# Process the sysinfo data, and update the node's attributes
			self.kernelVersion = sysInfo.attrib['kernel']
			self.dmthinp = True if sysInfo.attrib['dmthinp'] == 'yes' else False
			self.btrfs = True if sysInfo.attrib['btrfs'] == 'yes' else False
			self.glusterVersion = sysInfo.attrib['glustervers']
			self.memGB = int(sysInfo.attrib['memsize']) / 1024**2
			self.cpuCount = int(sysInfo.attrib['cpucount'])
			self.raidCard = sysInfo.attrib['raidcard']
			
			# Process the disk information
			for disk in freeDisks:
				deviceName = disk.attrib['device']
				sizeMB = int(disk.attrib['sizeKB']) / 1024
				
				brick = GlusterDisk(self.nodeName, deviceName, sizeMB)
				if self.localNode:
					brick.localDisk = True
				self.diskList[deviceName] = brick
				

		else:
			# Insert Scan failed logic here!
			pass
		
				
		g.LOGGER.debug('%s getDisks found %d devices on %s', time.asctime(), len(self.diskList), self.nodeName)
		
class GlusterCluster:
	""" Future - hold references to nodes in a cluster object """
	def __init__(self):
		pass
		

if __name__ == '__main__':
	main()

