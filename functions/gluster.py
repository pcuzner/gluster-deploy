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
from xml.dom import minidom
import logging
import time
import os

glusterLog = logging.getLogger()

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
	
	

def getPeers():
	"""	Run peer status to get a list of peers on the current server """
	pass
	return
	
def peerProbe(clusterState):
	"""	Receive an object containing a list of nodes to form a cluster """

	# create a copy of the nodes to work from 
	nodes = list(clusterState.targetList)
	
	for thisNode in nodes:

		clusterState.targetList.remove(thisNode)
		
		probeOutput = issueCMD("gluster peer probe " + thisNode)
		
		if ('failed' in probeOutput[0]) or ('invalid' in probeOutput[0]):
			# update the clusterState properties
			glusterLog.debug("%s peer probe for %s failed", time.asctime(), thisNode)
			clusterState.failureList.append(thisNode)
		else:
			# update the clusterState properties
			glusterLog.debug("%s peer probe for %s succeeded", time.asctime(), thisNode)
			clusterState.successList.append(thisNode)

	return 

class GlusterNode:
	def __init__(self, nodeName):
		self.nodeName = nodeName
		self.userName = 'root'
		self.userPassword = ''
		self.inCluster = False
		self.hasKey = False
		self.diskScanned = False
		self.brickCreated = False
		self.diskList = {}
		
	def pushKey(self):
		""" push the local machines root account ssh key to this node """
		
		#(nodeName, nodePassword) = nodeData.split('*')
		
		#keyState.targetList.remove(nodeName)
		
		sshTarget = SSHsession(self.userName, self.nodeName, self.userPassword)
		copyRC = sshTarget.sshCopyID()
		
		if copyRC <= 4:
			#keyState.successList.append(nodeName)
			glusterLog.info('%s ssh key added successfully to %s', time.asctime(), self.nodeName)
			self.hasKey = True
		else:
			#keyState.failureList.append(nodeName)
			glusterLog.info('%s Adding ssh key to %s failed', time.asctime(), self.nodeName)
			self.hasKey = False
			
		
	def joinCluster(self):
		"""	run peer probe against this node """
		probeOutput = issueCMD("gluster peer probe " + self.nodeName)
		
		if ('failed' in probeOutput[0]) or ('invalid' in probeOutput[0]):
			# update the clusterState properties
			glusterLog.debug("%s peer probe for %s failed", time.asctime(), self.nodeName)
			#clusterState.failureList.append(thisNode)
			self.inCluster = False
		else:
			# update the clusterState properties
			glusterLog.debug("%s peer probe for %s succeeded", time.asctime(), self.nodeName)
			#clusterState.successList.append(thisNode)
			self.inCluster = True
		pass
		
	def getDisks(self):
		"""	pass a scan script to the node to populate the nodes diskList """

		glusterLog.debug('%s getDisks scanning %s', time.asctime(), self.nodeName)
		
		
		# SOLVE ME - need a method for getting the absolute path of the script 
		scriptPath = '/root/gluster-deploy/scripts/findDevs.py'
		
		
		glusterLog.debug('%s getDisks using script from %s', time.asctime(), scriptPath)

		#sshPython runs the script, returning a list containing ',' separated values of disk <spc> size
		sshTarget = SSHsession(self.userName, self.nodeName, self.userPassword)
		diskData = sshTarget.sshPython(scriptPath)
		self.diskScanned = True

		if len(diskData) > 0:
			for diskInfo in diskData:
				
				(deviceName,sizeStr) = diskInfo.split(" ")
				size = int(sizeStr) / 1024**2						# convert to KB -> GB
				self.diskList[deviceName] = size
		
				
		glusterLog.debug('%s getDisks found %d devices on %s', time.asctime(), len(self.diskList), self.nodeName)
		

if __name__ == '__main__':
	main()

