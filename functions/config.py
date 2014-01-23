#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  config.py
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
import logging
import os
import sys
from functions.utils import MsgStack



def init():
	""" Initialise global variables """
	global LOGFILE
	global LOGLEVEL
	global ACCESSKEY
	global LOGGER
	global SVCPORT
	global HTTPPORT
	global NICPREFIX
	global PGMROOT
	global MSGSTACK
	global BTRFSKERNEL
	global SERVERLIST
	global BRICKPATH
	global VGNAME
	global LVNAME

	
	LOGFILE = 'gluster-deploy.log'
	LOGLEVEL = logging.getLevelName('DEBUG')		# DEBUG | INFO | ERROR
	
	logging.basicConfig(filename=LOGFILE, 
					level=LOGLEVEL, 
					filemode='w')
	
	LOGGER = logging.getLogger()
	
	# NIC types that would be presented to the admin for subnet
	# selection
	NICPREFIX = ('eth', 'bond', 'em','virbr0','ovirtmgmt','rhevm')
	
	# TCP port for glusterd
	SVCPORT = 24007
	
	# Default port for the web UI
	HTTPPORT = 8080
	
	# create a msgstack object used to track task progress
	MSGSTACK = MsgStack()
	
	# Minimum kernel version required to support btrfs filesystem bricks
	BTRFSKERNEL = 3.6
		
	PGMROOT = os.path.split(os.path.abspath(os.path.realpath(sys.argv[0])))[0]
	# glusterNodes
	
	# List of servers specified through the config file (deploy.cfg)
	SERVERLIST = []
	
	# default path for the gluster brick to be bound to
	BRICKPATH = "/gluster/brick1"
	VGNAME = "gluster"
	LVNAME = "gluster"


