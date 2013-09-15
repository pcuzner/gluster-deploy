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

class TaskProgress:
	def __init__(self, targetList=[]):
		self.targetList = targetList
		self.successList = []
		self.failureList = []

	def query(self):
		successCount = len(self.successList)
		failureCount = len(self.failureList)
		return (successCount, failureCount)

	def queryFull(self):
		pass
		
	def check(self):
		pass




if __name__ == '__main__':
	pass

