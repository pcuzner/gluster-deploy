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
# TODO 
#  1. review the logging capability and how to set by variable

from functions.network import getSubnets,findService, getHostIP
from functions.syscalls import issueCMD, generateKey, distributeKeys
from functions.glusterInterface import peerProbe
from functions.utils import TaskProgress


import logging
import BaseHTTPServer
import SimpleHTTPServer
import time
import os

HTTPPORT=8080
SVCPORT=24007

PASSWDFILE='www/js/accessKey.js'
LOGFILE='gluster-deploy.log'


LOGLEVEL=logging.getLevelName('DEBUG')		# DEBUG | INFO | ERROR




class RequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
		 
	def do_POST(self):
		""" Handle a post request looking at it's contents to determine
			the action to take.
		"""
		
		length = int(self.headers.getheader('content-length'))        
		dataString = self.rfile.read(length)
		
		cmd = dataString.split('|')[0]
		parms = dataString.split('|')[1:]
		
			
		if (cmd == "subnetList"):
			subnets = getSubnets()
			subnetString = ' '.join(subnets)
			
			logging.debug("%s network.getSubnets found - %s", time.asctime(), subnetString)
				
			self.wfile.write(subnetString)
			
		elif (cmd == "findNodes"):
			scanTarget= parms[0]
			
			logging.info('%s network.findService starting to scan %s', time.asctime(), scanTarget)
			nodeList = findService(scanTarget,SVCPORT)
			
			logging.info('%s network.findService scan complete', time.asctime())
			logging.debug("%s network.findService found %s services on %s", time.asctime(), str(len(nodeList)), scanTarget)

			self.wfile.write(" ".join(nodeList))
		
		elif (cmd == "createCluster"):

			targetList = parms[0].split(" ")			
			clusterState = TaskProgress(targetList)
			
			logging.info('%s createCluster joining %s nodes to the cluster', time.asctime(), len(targetList))

			# run peer probe to try and add nodes to the cluster
			peerProbe(clusterState)
			
			(success,failed) = clusterState.query()
			
			logging.debug('%s createCluster results - success %d, failed %d',time.asctime(), success, failed)

			# return success and failed counts to the caller (webpage)			
			retString = str(success) + " " + str(failed)
			self.wfile.write(retString)
			
			logging.info('%s gluster.createCluster complete', time.asctime())			
		
		elif (cmd == "queryCluster"):
			pass
		
		elif (cmd == "pushKeys"):
			keyData = parms[0].split(" ")
			targetList = []
			for n in keyData:
				[nodeName, nodePassword] = n.split('*')
				targetList.append(nodeName)

			keyState = TaskProgress(targetList)
			
			logging.info('%s pushKeys distributing ssh keys to %d nodes', time.asctime(), len(targetList))
			
			distributeKeys(keyState, keyData)

			(success, failed) = keyState.query()
			
			retString = str(success) + " " + str(failed)
			self.wfile.write(retString)
			
			logging.info('%s pushKeys complete - success %d, failed %d', time.asctime(), success, failed)

			
		elif (cmd == "queryKeys"):
			pass
			
			
		elif (cmd == "getDisks"):
			disksState = TaskProgress()
			
		elif (cmd == "queryDisks"):
			pass
		
			
		elif (cmd == "buildBricks"):
			brickState = TaskProgress()
		
		elif (cmd == "queryBuild"):
			pass
		

		

	def log_message(self, format, *args):
		""" Override std log_message method to record http messages 
			only when our loglevel is debug """
			
		if LOGLEVEL == 10:				# 10 = DEBUG, 20=INFO, 30=WARN
			logging.debug("%s %s %s", time.asctime(), self.address_string(), args)
		return

def updateKeyFile(accessKey):
	"""	Update the keyfile that holds this sessions access password """
	
	# TODO: This is a hack and needs to be replaced by an ajax call!
	
	pwdFile = open(PASSWDFILE,'w')
	pwdFile.write("var accessKey = '%s'" % accessKey)
	pwdFile.close()

def sshKeyOK():
	"""	
		Ensure local ssh key is in place, if not create it ready to be 
		distributed to the other nodes
	"""
	
	keyOK = False	
	
	if os.path.exists('/root/.ssh/id_rsa.pub'):
		keyOK = True
		logging.info('%s root has an ssh key ready to push out', time.asctime())
	else:
		genOut = issueCMD("ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa")
		for line in genOut:
			if 'Your public key has been saved' in line:
				logging.info('%s SSH key has been generated successfully', time.asctime())
				keyOK = True
				break
		
	return keyOK


def main():
	""" main control routine """
	
	logging.basicConfig(filename=LOGFILE, 
						level=LOGLEVEL, 
						filemode='w')
	
	accessKey = generateKey()

	hostIPs = getHostIP()
	
	print "\ngluster-deploy starting"
	
	# Program relies on ssh key distrubution and passwordless ssh login across
	# nodes, so if we can't get an sshkey generated...GAME OVER...
	if sshKeyOK():
		
		print "\n\tWeb server details:"
		print "\t\tAccess key  - " + accessKey
		print "\t\tWeb Address - "
		for i in hostIPs:
				print "\t\t\thttp://" + i + ":8080/"	
				
		updateKeyFile(accessKey)							# Hack - password should be an xml call
		
	
		# Create a basic httpd class
		serverClass = BaseHTTPServer.HTTPServer
		
		httpd = serverClass(("",HTTPPORT), RequestHandler)
		logging.info('%s http server started on using port %s', time.asctime(), HTTPPORT)
		
		try:
			# Run the httpd service
			httpd.serve_forever()
			
			# User has hit CTRL-C, so catch it to stop an error being thrown
		except KeyboardInterrupt:
			pass
			
		httpd.server_close()
		logging.info('%s http server stopped', time.asctime())	
		
		print '\ngluster-deploy web server stopped by user - CTRL-C\n'
	else:
		print '\n\n-->Problem generating an ssh key, program aborted\n\n'
		
	print 'gluster-deploy stopped.'
		

if __name__ == '__main__':
	

	
	main()

