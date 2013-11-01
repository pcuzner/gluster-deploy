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
#import sys

# PGMROOT = os.path.split(os.path.abspath(os.path.realpath(sys.argv[0])))[0]

# glusterLog = logging.getLogger()

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
	return issueCMD('gluster pool list')[1:]
	
def createVolume(xmlString):
	"""	function to define a gluster volume given an xml volume definition """
	
	cmdQueue = []
	bricks = []	
	xmlRoot = ETree.fromstring(xmlString)
	retCode = 0
	
	
	# Volume parameters
	volName = xmlRoot.find('./volume').attrib['name']
	volType = xmlRoot.find('./volume').attrib['type']
	useCase = xmlRoot.find('./volume').attrib['usecase']
	replicaParm = ' ' if ( xmlRoot.find('./volume').attrib['replica'] == 'none') else (' replica ' + xmlRoot.find('./volume').attrib['replica'])
	
	# protocols
	NFSstate  = 'nfs.disable off'  if ( xmlRoot.find('./volume/protocols').attrib['nfs'] == 'true' )  else 'nfs.disable on'
	CIFSstate = 'user.cifs enable' if ( xmlRoot.find('./volume/protocols').attrib['cifs'] == 'true' ) else 'user.cifs disable'
	
	# bricks
	for child in xmlRoot.findall('./volume/bricklist/brick'):
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
	
	if useCase.lower() == 'virtualisation':
		
		# look to see what type of virt target it is
		target = xmlRoot.find('./volume/tuning').attrib['target']
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
			
			# Is the virt group is available to use
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
	stepNum = 1
	for cmd in cmdQueue:
		cmdOutput = issueCMD(cmd)
		
		if cmdOutput[0] == 0:	# retcode is 1st element, so check it's 0
			
			# push this cmd to the queue for reporting in the UI
			g.LOGGER.info("%s step %d/%d successful", time.asctime(), stepNum, numCmds)
			g.LOGGER.debug("%s Command successful : %s", time.asctime(), cmd)
			pass
			# Log the cmd being run as successful
		else:
			g.LOGGER.info("%s vol create step failed", time.asctime())
			g.LOGGER.debug("%s command failure - %s", time.asctime(), cmd)
			# problem executing the command, log the response and return
			retCode = 8
			break
		stepNum +=1

	
	
	return retCode
	

def getPeers():
	"""	Run peer status to get a list of peers on the current server """
	pass
	return
	
#def peerProbe(clusterState):
	#"""	Receive an object containing a list of nodes to form a cluster """

	## create a copy of the nodes to work from 
	#nodes = list(clusterState.targetList)
	
	#for thisNode in nodes:

		#clusterState.targetList.remove(thisNode)
		
		#probeOutput = issueCMD("gluster peer probe " + thisNode)
		
		#if probeOutput[0] > 0:		# Check RC
			## update the clusterState properties
			#g.LOGGER.debug("%s peer probe for %s failed", time.asctime(), thisNode)
			#clusterState.failureList.append(thisNode)
		#else:
			## update the clusterState properties
			#g.LOGGER.debug("%s peer probe for %s succeeded", time.asctime(), thisNode)
			#clusterState.successList.append(thisNode)

	#return 

class GlusterDisk:
	def __init__(self,nodeName,deviceID, size,formatRequired=False):
		self.nodeName = nodeName
		self.deviceID = deviceID
		self.sizeGB = size
		self.formatRequired = formatRequired
		self.formatComplete = False
		self.mountPoint = ""
		self.snapReserved = 0
		self.workload = ""
		self.vgName = ""
		self.localDisk = False
		
	def formatBrick(self,userPassword,vgName,snapSpace,mountPoint,workload):
		"""	Pass the node the format script for this brick """
		
		self.mountPoint = mountPoint
		self.snapReserved = snapSpace
		self.workload = workload
		self.vgName = vgName
		
		g.LOGGER.debug('%s formatting %s as a brick on %s', time.asctime(), self.deviceID, self.nodeName )

		scriptPath = os.path.join(g.PGMROOT,'scripts/formatBrick.sh')
		scriptParms = " -d %s -v %s -s %s -m %s -w %s"%(self.deviceID, vgName, snapSpace, mountPoint, workload)


		scriptName = scriptPath + scriptParms

		if self.localDisk:
			resp = issueCMD(scriptName)
			rc=resp[0]
			# Error checking?
			# if all is well set the brick formatted boolean
			self.formatComplete = True
		else:
			
			ssh=SSHsession('root',self.nodeName,userPassword)
			resp=ssh.sshScript(scriptName)
			rc=resp[0]
			# Error checking?
			self.formatComplete = True
			
		
		g.LOGGER.debug('%s formatBrick complete on %s', time.asctime(), self.nodeName)
		
		return 0			

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
		probeOutput = issueCMD("gluster peer probe " + self.nodeName)
		
		if probeOutput[0] > 0:
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
		"""	pass a scan script to the node to populate the nodes diskList """

		g.LOGGER.debug('%s getDisks scanning %s', time.asctime(), self.nodeName)
		
		scriptName = os.path.join(g.PGMROOT,'scripts/findDevs.py')
		
		g.LOGGER.debug('%s getDisks using script from %s', time.asctime(), scriptName)

		#sshPython runs the script, returning a list containing ',' separated values of disk <spc> size
		
		# check if this is the local node, if so, use issueCMD not ssh
		if self.localNode:
			diskOut =  issueCMD(scriptName)
			rc = diskOut[0]
			diskData = diskOut[1:]

		else:
			sshTarget = SSHsession(self.userName, self.nodeName, self.userPassword)
			diskData = sshTarget.sshPython(scriptName)
			
			
		self.diskScanned = True

		if len(diskData) > 0:
			for diskInfo in diskData:
				
				(deviceName,sizeStr) = diskInfo.split(" ")
				size = int(sizeStr) / 1024**2						# convert to KB -> GB
				thisDisk = GlusterDisk(self.nodeName, deviceName, size)
				if self.localNode:
					thisDisk.localDisk = True
				self.diskList[deviceName] = thisDisk
		
				
		g.LOGGER.debug('%s getDisks found %d devices on %s', time.asctime(), len(self.diskList), self.nodeName)
		
		

if __name__ == '__main__':
	main()

