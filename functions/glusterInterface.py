#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  glusterInterface.py
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

from syscalls import issueCMD
from xml.dom import minidom
import logging
import time

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
		self.diskList = []
		
	def pushKeys(self):
		""" push the local machines root account ssh key to this node """
		
		pass
		
	def joinCluster(self):
		"""	run peer probe against this node """
		pass
		
	def getDisks(self):
		"""	return candidate disks from this node """
		pass


def main():
	
	return 0

if __name__ == '__main__':
	main()

