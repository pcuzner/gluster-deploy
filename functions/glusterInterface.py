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
	
def peerProbe(nodeList):
	"""	Receive a list of nodes to form a cluster """

	nodes = nodeList.split(" ")
	success = 0
	failed = 0
		
	glusterLog.debug("%s Gluster 'peer probe' for %d nodes started", time.asctime(), len(nodes))
	
	for thisNode in nodes:
		probeOut = issueCMD("gluster peer probe " + thisNode)
		if ('failed' in probeOut[0]) or ('invalid' in probeOut[0]):
			failed += 1
		else:
			success += 1
			
	glusterLog.debug("%s peer probe results - Success: %d, Failed: %d", time.asctime(), success, failed) 
			
	return (success,failed)


def main():
	
	return 0

if __name__ == '__main__':
	main()

