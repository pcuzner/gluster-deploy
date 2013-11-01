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



from functions.network import getSubnets,findService, getHostIP
from functions.syscalls import issueCMD, generateKey
from functions.gluster import GlusterNode, createVolume
# from functions.utils import TaskProgress		... FUTURE

import functions.globalvars as g					# Import globals shared across the modules

from optparse import OptionParser					# command line option parsing

import xml.etree.ElementTree as ETree

import logging
import BaseHTTPServer
import SimpleHTTPServer
import time
import os
import sys


# define a dict to hold gluster node objects, indexed by the node name
glusterNodes = {}	


class RequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
		 
	def do_POST(self):
		""" Handle a post request looking at it's contents to determine
			the action to take.
		"""
		
		
		length = int(self.headers.getheader('content-length'))        
		dataString = self.rfile.read(length)
		
		cmd = dataString.split('|')[0]
		parms = dataString.split('|')[1:]
		
		if cmd == "passwordCheck":
			
			if g.PASSWORDCHECK:
				xmlString = parms[0]
			
				# Read the xml string, and extract the password the user has supplied
				# <data><password>PASSWORD_STRING</password></data>		
				xmlRoot = ETree.fromstring(xmlString)
				userKey = xmlRoot.find('password').text
				
				if userKey == g.ACCESSKEY:
					g.LOGGER.debug('%s passwordCheck matched users access key',time.asctime())
					retString = 'OK'
				else:
					g.LOGGER.debug('%s passwordCheck unable to match users password(%s)',time.asctime(),userKey)
					retString = 'NOTOK'

			else:
				# PASSWORDCHECK turned off so just return OK
				g.LOGGER.info('%s passwordCheck bypassed by -n parameter',time.asctime())
				retString = 'OK'
				
			self.wfile.write(retString)	
				
			
		elif (cmd == "subnetList"):

			subnets = getSubnets()
			subnetString = ' '.join(subnets)
			
			g.LOGGER.debug("%s network.getSubnets found - %s", time.asctime(), subnetString)
			
			print "\t\tHost checked for active NIC's"				
			self.wfile.write(subnetString)
			
		elif (cmd == "findNodes"):
			scanTarget= parms[0]
			
			g.LOGGER.info('%s network.findService starting to scan %s', time.asctime(), scanTarget)
			nodeList = findService(scanTarget,g.SVCPORT)
					
			g.LOGGER.info('%s network.findService scan complete', time.asctime())
			g.LOGGER.debug("%s network.findService found %s services on %s", time.asctime(), str(len(nodeList)), scanTarget)

			print "\t\tSubnet scanned for glusterd ports - " + str(len(nodeList)) + " found"
			self.wfile.write(" ".join(nodeList))
		
		elif (cmd == "createCluster"):

			nodeList = parms[0].split(" ")	
			success = 0 
			failed = 0
			g.LOGGER.info('%s createCluster joining %s nodes to the cluster', time.asctime(), len(nodeList))
						
			# create the node objects and add to the management dict		
			for node in nodeList:

				if node.endswith('*'):
					# this is the local node, lose the last char
					node = node[:-1]
					glusterNodes[node] = GlusterNode(node)
					glusterNodes[node].localNode = True

					# create a node object and set to local
					# no need for joincluster or success/fail increment on the local node
					pass
				else:
					# create a node object
					glusterNodes[node] = GlusterNode(node)

					glusterNodes[node].joinCluster()
					if glusterNodes[node].inCluster:
						success += 1
					else:
						failed +=1
				
			
			
			g.LOGGER.debug('%s createCluster results - success %d, failed %d',time.asctime(), success, failed)
			
			print "\t\tCluster created - added " + str(success) + " nodes to this node (" + str(failed) + " nodes failed)"

			# return success and failed counts to the caller (webpage)			
			retString = str(success) + " " + str(failed)
			self.wfile.write(retString)
			
			g.LOGGER.info('%s gluster.createCluster complete', time.asctime())			
		
		elif (cmd == "queryCluster"):
			pass
		
		elif (cmd == "pushKeys"):
			
			keyData = parms[0].split(" ")
			#print keyData
			success = 0
			failed = 0
			
			g.LOGGER.info('%s pushKeys distributing ssh keys to %d nodes', time.asctime(), len(keyData))

			for n in keyData:
				[nodeName, nodePassword] = n.split('*')
				glusterNodes[nodeName].userPassword = nodePassword
				glusterNodes[nodeName].pushKey()
				if glusterNodes[nodeName].hasKey:
					success += 1
				else:
					failed += 1

			
			retString = str(success) + " " + str(failed)
			self.wfile.write(retString)
			
			g.LOGGER.info('%s pushKeys complete - success %d, failed %d', time.asctime(), success, failed)
			print "\t\tSSH keys distributed"
			
		elif (cmd == "queryKeys"):
			pass
			
			
		elif (cmd == "findDisks"):
			# receive the same list as sent to the keys
			# it only makes sense to try to get disk info from the successful
			# nodes where the ssh key copy worked
			
			retString = '<cluster>'
			diskCount = 0
			
			g.LOGGER.info('%s findDisks invoked', time.asctime())
			for node in sorted(glusterNodes.iterkeys()):
				
				# Scan this node for unused disks
				glusterNodes[node].findDisks()
				
				# Look at this nodes diskList - if it's not empty add it to an XML string 
				# to return to the caller
				if glusterNodes[node].diskList:
					#print glusterNodes[node].diskList
				
					retString = retString + "<node><nodename name='" + node + "'/><disks>"
					for deviceID in glusterNodes[node].diskList:
						diskObj = glusterNodes[node].diskList[deviceID]
						retString = retString + "<device id='" + deviceID + "' size='" + str(diskObj.sizeGB) + "' />"
						diskCount += 1
					retString = retString + "</disks></node>"

			retString = retString + "</cluster>"

			self.wfile.write(retString)
			
			g.LOGGER.info('%s findDisks complete', time.asctime())
			print "\t\tNodes scanned for available (free) disks (" + str(diskCount) + " found)"
			
			
		elif (cmd == "queryDisks"):
			pass
		
			
		elif (cmd == "registerBricks"):
			diskXML = parms[0]
			
			xmlRoot = ETree.fromstring(diskXML)
			for device in xmlRoot:
				targetHost = device.attrib['host']
				targetDevice = device.attrib['device']
				
				disk = glusterNodes[targetHost].diskList[targetDevice]
				disk.formatRequired=True 
			
			# brickState = TaskProgress()
			# return an update complete message back to the caller
			self.wfile.write('OK')
			pass
		

		elif (cmd == "buildBricks"):
			parmsXML = parms[0]
			
			# process the parameter XML file to set variables up for the script			
			xmlRoot = ETree.fromstring(parmsXML)
			
			useCase = xmlRoot.find('./parms').attrib['usecase']
			snapReserve = xmlRoot.find('./parms').attrib['snapreserve']
			vgName = xmlRoot.find('./parms').attrib['volgroup']
			mountPoint = xmlRoot.find('./parms').attrib['mountpoint']

			brickList = []	# Maintain a list of bricks that were formatted
			
			for node in sorted(glusterNodes.iterkeys()):
				pass
				thisHost = glusterNodes[node]
				# take a look at this nodes disk list 
				# for each disk with formatrequired
				# 	call the formatbrick method
				# 	if ret_code is ok update the state of the brick and post message to queue(future)
				if thisHost.diskList:
					
					for diskID in thisHost.diskList:
						thisDisk = thisHost.diskList[diskID]
						
						if thisDisk.formatRequired:
							g.LOGGER.debug('%s format requested for node %s, disk %s',time.asctime(), node, thisDisk.deviceID)
							
							# issue command, get rc

							thisDisk.formatBrick(thisHost.userPassword,vgName,snapReserve,mountPoint,useCase)
							brickList.append(thisDisk)

							#if state == 0:
								# set message success
							#	pass
							#else:
								# set message failed
							#	pass
			
			# Future: check the brickList to only allow bricks of the same size through to vol create
			
			# Now the bricks have been formatted, we process the list
			# to assemble an xml string ready for the UI to load into an
			# array for use in the volCreate step				
			xmlDoc =  "<data>"
			xmlDoc += "<summary success='0' failed='0' />"
			
			for brick in brickList:
				# e.g. <brick fsname='/gluster/brick' size='10' servername='rhs1-1' />"
				xmlDoc += "<brick fsname='" + brick.mountPoint + "' size='" + str(brick.sizeGB) + "' servername='" + brick.nodeName + "' />"
			xmlDoc += "</data>"

			# Send to UI
			self.wfile.write(xmlDoc)
			
			print "\t\tBricks formatted"

		
		elif (cmd == "queryBuild"):
			pass		

		elif (cmd == "volCreate"):
			g.LOGGER.info('%s Initiating vol create process', time.asctime())
			rc = createVolume(parms[0])

			if rc == 0:
				# Create volume was successful
				g.LOGGER.info('%s Volume creation was successful', time.asctime())
				msg = 'success'
				pass
			else:
				# Problem creating the volume
				g.LOGGER.info('%s Volume creation failed rc=%d', time.asctime(), rc)
				msg = 'failed'
				pass
				
			self.wfile.write(msg)	
			
			print "\t\tVolume create result: " + msg		
			
			
		elif (cmd == "quit"):
			# Update the httpd servers state, so the run forever loop can be exited
			self.server.stop = True
			
			print "\t\tQuit received from the UI, shutting down\n"
			

	def log_message(self, format, *args):
		""" Override std log_message method to record http messages 
			only when our loglevel is debug """
			
		if g.LOGLEVEL == 10:				# 10 = DEBUG, 20=INFO, 30=WARN
			g.LOGGER.debug("%s %s %s", time.asctime(), self.address_string(), args)
		return

class StoppableHTTPServer (BaseHTTPServer.HTTPServer):
	""" Standard HTTPServer extended with a Stop capability """
	
	def serve_forever(self):
		""" Overridden method to insert the stop process """
		self.stop = False
		
		while not self.stop:
			self.handle_request()


def sshKeyOK():
	"""	
		Ensure local ssh key is in place, if not create it ready to be 
		distributed to the other nodes
	"""
	
	keyOK = False	
	
	if os.path.exists('/root/.ssh/id_rsa.pub'):
		keyOK = True
		g.LOGGER.info('%s root has an ssh key ready to push out', time.asctime())
	else:
		
		# Run ssh-keygen, in shell mode to generate the key i.e. use the 'True' parameter
		genOut = issueCMD("ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa",True)
		for line in genOut:
			if 'Your public key has been saved' in line:
				g.LOGGER.info('%s SSH key has been generated successfully', time.asctime())
				keyOK = True
				break
		
	return keyOK


def main():
	""" main control routine """
	
	
	#g.LOGGER.basicConfig(filename=LOGFILE, 
	#					level=LOGLEVEL, 
	#					filemode='w')
	
	#accessKey = generateKey()

	hostIPs = getHostIP()
	
	print "\ngluster-deploy starting"
	
	# Program relies on ssh key distrubution and passwordless ssh login across
	# nodes, so if we can't get an sshkey generated...GAME OVER...
	if sshKeyOK():
		
		keyMsg = '' if g.PASSWORDCHECK else ' (Bypassed with the -n option)'
		
		print "\n\tWeb server details:"
		print "\t\tAccess key  - " + g.ACCESSKEY + keyMsg
		print "\t\tWeb Address - "
		for i in hostIPs:
			print "\t\t\thttp://" + i + ":" + str(g.HTTPPORT) + "/"	
		
		print "\n\tSetup Progress"
				
		#updateKeyFile(ACCESSKEY)							# Hack - password should be an xml call
		
	
		# Create a basic httpd class
		#serverClass = BaseHTTPServer.HTTPServer
		
		# httpd = serverClass(("",HTTPPORT), RequestHandler)
		httpd = StoppableHTTPServer(("",g.HTTPPORT), RequestHandler)
		
		g.LOGGER.info('%s http server started on using port %s', time.asctime(), g.HTTPPORT)
		
		try:
			# Run the httpd service
			httpd.serve_forever()
			
			# User has hit CTRL-C, so catch it to stop an error being thrown
		except KeyboardInterrupt:
			print '\ngluster-deploy web server stopped by user hitting - CTRL-C\n'
			
			
		httpd.server_close()
		
		g.LOGGER.info('%s http server stopped', time.asctime())	

	else:
		print '\n\n-->Problem generating an ssh key, program aborted\n\n'
		
	print '\ngluster-deploy stopped.'
		

if __name__ == '__main__':

	usageInfo = "usage: %prog [options]"
	
	parser = OptionParser(usage=usageInfo,version="%prog 0.2")
	parser.add_option("-n","--no-password",dest="skipPassword",action="store_true",default=False,help="Skip access key checking (debug only)")
	(options, args) = parser.parse_args()
	
	g.init()		# Initialise the global variables
	
	g.PASSWORDCHECK = not options.skipPassword
	
	g.ACCESSKEY = generateKey()
	
	
	main()

