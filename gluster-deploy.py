#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  gluster-deploy.py
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
# FUTURES 
#  1. Code written for python 2.6 and above. optparse changes to argparse in 2.7 onwards
#     so code changes will be necessary later
#

import logging
import time
import os

from threading 	import active_count,enumerate
from optparse 	import OptionParser			# command line option parsing

from 	functions.network 		import getHostIP
from 	functions.syscalls 		import issueCMD, generateKey
from 	functions.utils 		import processConfigFile
from 	functions.webservices 	import RequestHandler, StoppableHTTPServer
import 	functions.config as cfg				# global variables/settings


def sshKeyOK():
	"""	Ensure local ssh key is in place, if not create it """

	keyOK = False	
	
	if os.path.exists('/root/.ssh/id_rsa.pub'):
		keyOK = True
		cfg.LOGGER.info('%s root has an ssh key ready to push out', time.asctime())
	else:
		
		# Run ssh-keygen, in shell mode to generate the key i.e. use the 'True' parameter
		(rc, genOut) = issueCMD("ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa",True)

		for line in genOut:
			if 'Your public key has been saved' in line:
				cfg.LOGGER.info('%s SSH key has been generated successfully', time.asctime())
				keyOK = True
				break
		
	return keyOK


def main():
	""" main control logic """
	

	hostIPs = getHostIP()
	cfg.LOGGER.info("%s Host has %s IP's to bind the web server to", time.asctime(), len(hostIPs))
	
	print "\ngluster-deploy starting"
	print "\n\tConfiguration file"
	
	if configFile:
		
		# user invoked with -f and has supplied a file that exists, so process it
		print "\t\tProcessing config file(" + configFile + ")"
		
		# config globals to use for nodes, brickpath etc
		processConfigFile(configFile)
		
		numServers = len(cfg.SERVERLIST)
		if numServers > 0:
			print "\n\t\tConfiguration file provided " + str(numServers) + " potentially usable nodes"
		else:
			print "\t\t-> No suitable nodes detected, UI will offer subnet selection/scan"	
			
	else:
		# no config file was specified at run time (default behaviour)
		print "\t\t-> Not supplied, program defaults will be used, together with\n\t\t   node discovery by subnet scan"
	
	
	# Program relies on ssh key distrubution and passwordless ssh login across
	# nodes, so if we can't get an sshkey generated...GAME OVER...
	if sshKeyOK():
		
		keyMsg = '' if cfg.PASSWORDCHECK else ' (Bypassed with the -n option)'
		
		print "\n\tWeb server details:"
		print "\t\tAccess key  - " + cfg.ACCESSKEY + keyMsg
		print "\t\tWeb Address - "
		for i in hostIPs:
			print "\t\t\thttp://" + i + ":" + str(cfg.HTTPPORT) + "/"	
		
		print "\n\tSetup Progress"
				
		httpd = StoppableHTTPServer(("",cfg.HTTPPORT), RequestHandler)
		
		cfg.LOGGER.info('%s http server started, listening on port %s', time.asctime(), cfg.HTTPPORT)
		
		try:
			# Run the httpd service
			httpd.serve_forever()
			
			# User has hit CTRL-C, so catch it to stop an error being thrown
		except KeyboardInterrupt:
			print '\ngluster-deploy web server stopped by user hitting - CTRL-C\n'

		# Wait for threads to quiesce
		print "\t\tWaiting for active threads(" + str(active_count()) + ") to quiesce"
		
		if active_count() > 1:
			threadList = enumerate()
			threadNames = [ t.getName() for t in threadList ]
			cfg.LOGGER.debug('%s http server threads running %s', time.asctime(), ','.join(threadNames))
			
		while active_count() > 1:
			try:
				time.sleep(0.1)
			except KeyboardInterrupt:
				break
		
		httpd.server_close()

		cfg.LOGGER.info('%s http server stopped', time.asctime())	

	else:
		print '\n\n-->Problem generating an ssh key, program aborted\n\n'
		
	print '\ngluster-deploy stopped.'
	
	exit()
		

if __name__ == '__main__':

	configFile = ""
	
	usageInfo = "usage: %prog [options]"
	
	parser = OptionParser(usage=usageInfo,version="%prog 0.7")
	parser.add_option("-n","--no-password",dest="skipPassword",action="store_true",default=False,help="Skip access key checking (debug only)")
	parser.add_option("-p","--port",dest="port",default=8080,type="int", help="Port to run UI on (> 1024)")
	parser.add_option("-f","--config-file",dest="cfgFile",type="string",help="Config file providing server list bypassing subnet scan")
	
	(options, args) = parser.parse_args()
	
	cfg.init()		# Initialise the global variables
	
	cfg.PASSWORDCHECK = not options.skipPassword
	
	cfg.ACCESSKEY = generateKey()
	
	if options.port:
		if options.port > 1024:
			cfg.HTTPPORT = options.port

	
	if options.cfgFile:

		# Configuration file supplied so call the parser to build a server
		# list of nodes to scan for the create cluster step
		if os.path.isfile(options.cfgFile):
			configFile = options.cfgFile
		else:	
			print "\n\tConfig file provided (" + options.cfgFile + "), but does not exist."
			print "\nRun aborted."
			exit(16)

	main()

