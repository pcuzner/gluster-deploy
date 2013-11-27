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

class MsgStack:
	""" Message stack used by the async processes to record step completion
		enabling the web UI to query current progress
	"""
	
	def __init__(self):
		self.messages = []
		self.lock = threading.Lock()

	def popMsgs(self):
		""" Funtion to pop the current entries from the list and return them
			to the caller
		"""
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
		

def kernelCompare(thisKernel, kernelTarget):	
	""" Receive two kernels versions, and return True/False if the given kernel is 
		>= the target kernel """ 
		
	result = False
	
	(k1version, k1release) = thisKernel.split('.')
	(k2version, k2release) = kernelTarget.split('.')
	
	if k1version == k2version:
		if int(k2release) >= int(k1release):
			result = True
			
	return result


if __name__ == '__main__':
	pass

