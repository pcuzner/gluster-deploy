#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  utils.py
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

import threading
import os
import ConfigParser						# renamed to configparser in python3!
import socket

import network							# local module



class MsgStack:
	""" 
	Class used to hold progress messages, enabling the current state to be queried
	and used by the UI
	"""
	
	def __init__(self):
		self.messages = []
		self.lock = threading.Lock()

	def popMsgs(self):
		""" Funtion to pop the current entries from the list and return them """

		msgList = []
		
		self.lock.acquire()
		if len(self.messages) > 0:
			msgList = list(self.messages)
			del self.messages[:]	# drop all current elements
		self.lock.release()

		return msgList
		
	def pushMsg(self,msg):
		""" Receive a msg and add it to the current message list """
		self.lock.acquire()
		self.messages.append(msg)
		self.lock.release()
		return
		

	def msgsQueued(self):
		""" Return a count of the size of the message stack """
		return len(self.messages)
		
	def reset(self):
		""" drop existing messages on the list """
		self.lock.acquire()
		del self.messages[:]
		self.lock.release()
		return

def kernelCompare(thisKernel, kernelTarget):	
	""" Receive current and target kernels, return true if the current is > target """
		
	result = False
	
	(k1version, k1release) = thisKernel.split('.')
	(k2version, k2release) = kernelTarget.split('.')
	
	if k1version >= k2version:
		if int(k2release) >= int(k1release):
			result = True
			
	return result


def buildServerList(configFileName, hostIPs):
	""" 
	Receive a user specfiied configuration file, process it to return a list of
	servers that will be looked at for active glusterd processes - to bypass the 
	subnet scan
	"""
	
	config = ConfigParser.ConfigParser()
	config.read(configFileName)
	
	try:
		nodeNames = config.get("nodes","nodenames").split()
	except:
		print "\t\t-> Error processing the config file, subnet scanning will be used"
		nodeNames = []		
	
	if nodeNames:
		for node in nodeNames:
			
			# process each node to make sure it's a valid IP or name
			# if not drop from the serverList
			if not network.hostOK(node):
				print "\t\t-> dropping " + node + " (name doesn't resolve, or IP is invalid)"
				nodeNames.remove(node)
			else:
				pass
				
			pass
		
	# return a sorted list	
	return sorted(nodeNames)

if __name__ == '__main__':
	pass

