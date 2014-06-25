#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  webservices.py
#  
#  Copyright 2014 Paul <paul@rhlaptop>
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

import BaseHTTPServer
import SimpleHTTPServer
import SocketServer
import httplib
import time
import xml.etree.ElementTree as ETree

import 	functions.config as cfg
from 	functions.network 		import getSubnets,findService
from 	functions.gluster		import Cluster, Volume, FormatDisks
from 	functions.syscalls		import getMultiplier
from 	functions.utils			import kernelCompare


def loadHTML(fileName):
	""" receive a html file to load, and return the file as a string to
		to the caller after removing any newline and tab characters
	"""
	
	with open(fileName) as htmlData:
		htmlStr = htmlData.read()
		htmlStr = htmlStr.replace('\t','').replace('\n','')
		
	return htmlStr

def nextPageXML(htmlFile, nextDiv=None):
	"""Append the given xml string with the additional elements enabling 
	the dynamic update of the webpage
	"""
	nextPageStr = "<page-info>"
	
	if nextDiv:
		nextPageStr += "<next-div div-name='" + nextDiv + "'/>"
	
	nextPageStr += ( "<div-contents><![CDATA["
				+ loadHTML(htmlFile)
				+ "]]></div-contents></page-info>")
				
	return nextPageStr


class RequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
	
	adminIP = ''
	pollingEnabled = False
	pollingEnabledTasks = ['build-bricks','vol-create', 'find-nodes']
	
	# define a list to hold a summary completion message added at the end 
	# of each phase of the 'wizard'
	taskLog = []

	def sendResponse(self,responseText,mimeType="text/xml"):
		"""Send the response back to the client """
		
		self.send_response(200)				# OK
		
		self.send_header("Content-type",mimeType)
		self.send_header("Content-length", len(responseText))
		self.end_headers()
						
		self.wfile.write(responseText)      
		
		#self.wfile.close()
	
	def __rqstPassword(self,xmlDoc):
		"""Receive password and return the response to be sent to caller
		"""
		
		if cfg.PASSWORDCHECK:
				
			userKey = xmlDoc.find('password').text
				
			if userKey == cfg.ACCESSKEY:
				cfg.LOGGER.debug('%s passwordCheck matched users access key',time.asctime())
				retString = 'OK'
			else:
				cfg.LOGGER.debug('%s passwordCheck unable to match users password(%s)',time.asctime(),userKey)
				retString = 'NOTOK'

		else:
			# PASSWORDCHECK turned off so just return OK
			cfg.LOGGER.info('%s passwordCheck bypassed by -n parameter',time.asctime())
			retString = 'OK'
			
		response = "<response><status-text>" + retString + "</status-text>"
			
		if retString == 'OK':
			# Append the next page html to the xml response
			response += nextPageXML('www/overview.html', 'overview')
						
		response += "</response>"
		
		return response
		
	def __rqstSubnetList(self):
		"""Provide the caller with a list of subnets on the active node
		to scan, or a list of the servers defined in the config file
		passed at runtime
		"""
		response = "<response>"

		# If there are servers in the SERVERLIST, we pass back the server IP/names not
		# subnets to allow subnet selection and scan to be bypassed
		if cfg.SERVERLIST:
			cfg.LOGGER.info("%s Bypassing subnet scan, using nodes from configuration file", time.asctime())
			respText = 'OK'
			response += "<request-type>servers</request-type>"
			
			msg = "Candidate servers provided by the configuration file (bypassing subnet scanning)"
			
		else:
			# server list has not been provided, so let look at the hosts IP config and 
			# get a list of subnets for the admin to choose from for the subnet scan

			subnets = getSubnets()
			
			if subnets:
				respText = "OK"
				response += "<request-type>scan</request-type>"
				for subnet in subnets:
					response += "<subnet>" + subnet + "</subnet>"

				allSubnets = ' '.join(subnets)
			
				cfg.LOGGER.debug("%s network.getSubnets found - %s", time.asctime(), allSubnets)
				
				msg = "Candidate servers will be determined by subnet scan"
			
			else:
				respText = "FAILED"
				msg = "ERROR - Unable to locate subnets on this host"
				
		response += "<status-text>"+respText+"</status-text>"
				
		if respText == 'OK':
			# lets provide the html for the node discovery page
			response += nextPageXML('www/nodes.html', 'nodes')
		
		response += "</response>"			
		
		RequestHandler.taskLog.append(msg)
		print "\t\t" + msg		
		
		return response	
		

	def __rqstFindNodes(self, xmlDoc):
		"""Determine a list of nodes with port 24007 (glusterd open) from
		either a subnet scan or scanning a list of servers provided by the 
		config file
		"""
		
		scanType = xmlDoc.find('scan-type').text
		
		if scanType == 'subnet':
			scanTarget = xmlDoc.find('subnet').text
			cfg.LOGGER.info('%s network.findService starting to scan %s', time.asctime(), scanTarget)
		elif scanType == 'serverlist':
			scanTarget = " ".join(cfg.SERVERLIST)
			cfg.LOGGER.info('%s network.findService processing server list', time.asctime())
		

		nodeList = findService(scanTarget,cfg.SVCPORT)
		
		if nodeList:
			response = "<response><status-text>OK</status-text>"
			for node in nodeList:
				response += "<node>" + node + "</node>"
			response += "</response>"
				
			cfg.LOGGER.info('%s network.findService scan complete', time.asctime())
			cfg.LOGGER.debug("%s network.findService found %d services", time.asctime(), len(nodeList))

		else:
			response = "<response><status-text>FAILED</status-text></response>"


		
		# Using the list of servers for the nodes completes really quickly, and they never get displayed
		# but stack in the message stack, appearing on the next tasks msg log. To prevent this, we drop
		# the msg stack.
		if scanType == 'serverlist':
			cfg.MSGSTACK.reset()

		msg = "%d candidate servers found that have glusterd running"%(len(nodeList))
		RequestHandler.taskLog.append(msg)
		print "\t\t" + msg
		
		RequestHandler.pollingEnabled = False		
					
		return response
		

	def __rqstCreateCluster(self, xmlDoc):
		"""Create the cluster by attempted to peer probe it
		"""
		nodeElements = xmlDoc.findall('node')
		nodeList = []
		for node in nodeElements:
			nodeList.append(node.text)

		success = 0 
		failed = 0
		cfg.LOGGER.info('%s createCluster joining %s nodes to the cluster', time.asctime(), (len(nodeList)-1))
					
		# create the node objects 
		for nodeName in nodeList:

			if nodeName.endswith('*'):
				# this is the local node, lose the last char
				nodeName = nodeName[:-1]
				
				# create a node object and set to local
				# no need for joincluster or success/fail increment on the local node
				cfg.CLUSTER.addNode(nodeName)
				cfg.CLUSTER.node[nodeName].localNode = True

			else:
				
				# create a node object
				cfg.CLUSTER.addNode(nodeName)
				
				if cfg.CLUSTER.node[nodeName].inCluster:
					success += 1
				else:
					failed +=1
			
		# Build XML response string
		respText = "OK" if failed == 0 else "FAILED"
		response = ( "<response><status-text>" + respText + "</status-text><summary success='" + str(success)
					+ "' failed='" + str(failed) + "' />")
		
		# Add the nodes successfully added to the response	(sorted for display purposes)		
		for nodeName in cfg.CLUSTER.nodeList():
			#if not cfg.CLUSTER.node[nodeName].localNode:
			response += "<node name='" + nodeName + "' />"
		
		# Pass the client the html and next div to use in the UI
		response += nextPageXML('www/keys.html','keys') + "</response>" 
		
		cfg.LOGGER.debug('%s createCluster results - success %d, failed %d',time.asctime(), success, failed)
		
		
		msg = "Cluster creation complete - %d nodes successful, %d nodes failed"%(success,failed)
		print "\t\t" + msg
		cfg.LOGGER.info('%s gluster.createCluster complete - %d successful, %d failed', time.asctime(), success, failed)
		
		# Add task completion state to the log
		RequestHandler.taskLog.append(msg)		
		
		return response

	def __rqstPushKeys(self, xmlDoc):
		"""Handle the distribution of the local users public key for passwordless
		ssh
		"""
		success = 0
		failed = 0
					
		nodes = xmlDoc.findall('node')
		for node in nodes:
			nodeName = node.attrib['server']
			nodePassword = node.attrib['password']
			
			thisNode = cfg.CLUSTER.node[nodeName]
			thisNode.userPassword = nodePassword
			thisNode.pushKey()
			if thisNode.hasKey:
				success += 1
			else:
				failed += 1

		cfg.LOGGER.info('%s pushKeys distributing ssh keys to %d nodes', time.asctime(), len(nodes))

		respText = "OK" if failed == 0 else "FAILED"
		response = ( "<response><status-text>" + respText + "</status-text><summary success='" 
					+ str(success) + "' failed='" + str(failed) + "' />")
					
		# Pass the client the html and next div to use in the UI
		response += nextPageXML('www/disks.html','disks') + "</response>" 
					
		cfg.LOGGER.info('%s pushKeys complete - success %d, failed %d', time.asctime(), success, failed)
		
		msg = "SSH keys distributed - %d successful, %d failed"%(success,failed)
		
		# Add task completion state to the log
		RequestHandler.taskLog.append(msg)
		
		print "\t\t" + msg		
		
		return response

	def __rqstFindDisks(self):
		"""Invoke the findDisks method that remotely executes the findDevs.py
		script on each node returning a list of free disks suitable for a 
		gluster deployment
		"""
		
		response = '<response>'
		diskCount = 0
		
		cfg.LOGGER.info('%s findDisks invoked', time.asctime())
		for nodeName in cfg.CLUSTER.nodeList():
			
			# Scan this node for unused disks
			thisNode = cfg.CLUSTER.node[nodeName]
			thisNode.findDisks()
			
			# Look at this nodes diskList - if it's not empty add it to an XML string 
			# to return to the caller
			if thisNode.diskList:
			
				response += "<node><nodename name='" + nodeName + "'/><disks>"
				for deviceID in sorted(thisNode.diskList):
					diskObj = thisNode.diskList[deviceID]
					sizeGB = diskObj.sizeMB / 1024
					response += "<device id='" + deviceID + "' size='" + str(sizeGB) + "' />"
					diskCount += 1
				response += "</disks></node>"

		response += "</response>"

		cfg.LOGGER.info('%s findDisks complete', time.asctime())
		
		msg = "Nodes scanned, %d candidate disks detected"%(diskCount)
		RequestHandler.taskLog.append(msg)
		print "\t\t" + msg		
		
		return response
		
	def __rqstRegisterBricks(self, xmlDoc):
		"""Flag the bricks chosen by the user signifying format required
		"""
		devices = xmlDoc.findall('device')
		
		# Cycle through the devices, and set the formatRequired flag
		for device in devices:
			targetHost = device.attrib['host']
			targetDevice = device.attrib['device']
			
			thisNode = cfg.CLUSTER.node[targetHost]
			
			brick = thisNode.diskList[targetDevice]
			brick.formatRequired=True 
		
		response = "<response><status-text>OK</status-text>"
		response += "<brick path='" + cfg.BRICKPATH + "' vgname='" + cfg.VGNAME + "' lvname='" + cfg.LVNAME + "' />"

		# get a list of common tuned profiles across all nodes to 
		# pass back to the UI
		tunedProfiles = cfg.CLUSTER.tunedProfiles()
		if len(tunedProfiles) > 1:
			for profName in tunedProfiles:
				response += "<tunedprofile>%s</tunedprofile>"%(profName)

		# Determine whether snapshots are available, by looking at the capabilities
		# of every node in the cluster. They must all tally for these features to be 
		# used.
		
		thinpSupport = "YES"
		btrfsSupport = "YES"

		
		# use a set to hold the unique glusterfs versions found across the nodes
		versionSet=set()
		
		# cycle through all nodes. They must ALL match to have snapshot or btrfs 
		# features enabled
		for nodeName in cfg.CLUSTER.nodeList():   
			thisNode = cfg.CLUSTER.node[nodeName]
			
			# just use Version/Release components of the version string
			thisVersion = '.'.join(thisNode.glusterVersion.split('.')[:2])
			versionSet.add(thisVersion)
			
			if thisNode.dmthinp == False:
				thinpSupport = "NO"
			if (thisNode.btrfs == False) or (not kernelCompare(thisNode.kernelVersion[:2])):
				btrfsSupport = "NO"
		
		# For the cluster to support gluster snapshots, all versions must be >=
		# SNAPSHOTVERSION. When this is set to NO, it causes a warning box in the
		# UI, when YES the use of snapshots is not warned against
		glfsSnapshotSupport = "YES"
		for v in versionSet:
				if v < cfg.SNAPSHOTVERSION:
					glfsSnapshotSupport = "NO"
		
		
		# Update the cluster's capability based on the findings from 
		# each node
		cfg.CLUSTER.capability['btrfs'] = btrfsSupport
		cfg.CLUSTER.capability['thinp'] = thinpSupport
		cfg.CLUSTER.glusterVersion = thisVersion if len(versionSet) == 1 else "MIXED - %s"%(','.join(versionSet))
		
		
		
		response += ("<features snapshot='" + thinpSupport + "' btrfs='"
					+ btrfsSupport + "' glustersnapshot='" + glfsSnapshotSupport + "' />")
		
		# Add the HTML for the next div - bricks.html
		response += nextPageXML('www/bricks.html', 'bricks') + "</response>"		
		
		return response

	def __rqstBuildBricks(self, xmlDoc):
		"""Initiate the format of the disks defined by the user as
		glusterfs bricks
		"""
		# Creating the bricks is done in two phases;
		#
		# 1. use the params from UI to set the parameters on each
		#    disk
		# 2. Initiate the format process by node (1 thread per node)
		#
		
		cfg.CLUSTER.resetOpStatus()
		brickList=[]
		
		# define the variables that define the configuration of the brick
		brickParms=['vgName','lvName','useCase','mountPoint','snapRequired', 'snapReserve','brickType','tuned']
		
		# process the parameter XML file from the UI 		
		parms = xmlDoc.find('brickparms')
		
		snapReserve = 0 									# default - no reserve
		useCase = parms.attrib['usecase'] 
		brickType = parms.attrib['brickprovider']			# LVM or BTRFS
		
		tuned = parms.attrib['tuned'] if 'tuned' in parms.attrib else ''
		
		snapRequired = parms.attrib['snaprequired']			# YES or NO
		lvTemplate = parms.attrib['lvname'] if ( brickType == 'LVM' ) else ""
		vgTemplate = parms.attrib['volgroup'] if (brickType == 'LVM') else ""
		pathTemplate = parms.attrib['mountpoint']
		
		if snapRequired == 'YES':
			snapReserve = int(parms.attrib['snapreserve'])
		
		# brickList will provide a list of the bricks for formatting
		brickList = []	
		
		# 1. Set up the brick's parameters
		for nodeName in cfg.CLUSTER.nodeList():

			thisNode = cfg.CLUSTER.node[nodeName]
			
			disks2Format = thisNode.formatCount()
			
			nodePath = pathTemplate
			nodeLV = lvTemplate
			nodeVG = vgTemplate
			
			if disks2Format > 0:
				
				if disks2Format > 1:
					# Set a suffix to add to mountpoint and lvname
					sfx = 1
					
					# adjust the template if it ends in a numeric
					if nodePath[-1].isdigit():
						nodePath = nodePath[:-1]
					if nodeLV[-1].isdigit():
						nodeLV = nodeLV[:-1]
					if nodeVG[-1].isdigit():
						nodeVG = nodeVG[:-1]

				for diskID in thisNode.diskList:
					thisDisk = thisNode.diskList[diskID]
					
					if thisDisk.formatRequired:
						cfg.LOGGER.debug('%s format requested for node %s, disk %s',time.asctime(), nodeName, thisDisk.deviceID)

						if disks2Format > 1:
							mountPoint = nodePath + str(sfx)
							lvName     = nodeLV + str(sfx)
							vgName     = nodeVG + str(sfx)
							sfx += 1
						else:
							mountPoint = pathTemplate
							lvName = lvTemplate
							vgName = vgTemplate
							
						settings={}
						for keyName in brickParms:
							settings[keyName] = eval(keyName)
							
						thisDisk.setParms(settings)	

						brickList.append(thisDisk)							

		# 2. Initiate the format threads
		threadList=[]
		for nodeName in cfg.CLUSTER.nodeList():
			
			thisNode = cfg.CLUSTER.node[nodeName]
			if thisNode.formatCount() > 0:
				
				newThread = FormatDisks(thisNode)
				newThread.start()
				threadList.append(newThread)
				
		for thread in threadList:
			thread.join()						# wait for all threads to complete
		
		# Remove any intended bricks from the list that have their failed
		# flag set
		for brick in brickList:
			
			if brick.formatStatus == "failed":
				brickList.remove(brick)
		
		# Now the bricks have been formatted, we process the list
		# to assemble an xml string ready for the volCreate UI page
		respText = 'OK' if (cfg.CLUSTER.opStatus['failed'] == 0 ) else 'FAILED'
		response = ( "<response><status-text>" + respText + "</status-text>"
					+ "<summary success='" + str(cfg.CLUSTER.opStatus['success']) 
					+ "' failed='" + str(cfg.CLUSTER.opStatus['failed']) + "' />" )
		
		for brick in brickList:
			
			# eg. <brick fsname='/gluster/brick' size='10' servername='rhs1-1' />
			sizeGB = ( brick.sizeMB / 1024 ) if brick.thinSize == 0 else ( brick.thinSize / 1024 )
			response += ("<brick fsname='" + brick.mountPoint
						+ "' size='" + str(sizeGB) + "' servername='" 
						+ brick.nodeName + "' />")
		
		# Populate the volCreate div, if all is well :)
		if respText == 'OK':
			response += nextPageXML('www/volCreate.html', 'volCreate')
		
		response += "</response>"

		msg = "%d candidate disks formatted as 'bricks', %d failed"%(cfg.CLUSTER.opStatus['success'],cfg.CLUSTER.opStatus['failed'])
		RequestHandler.taskLog.append(msg)
		
		print "\t\t"+msg

		RequestHandler.pollingEnabled = False		
		
		return response
		

	def __rqstVolCreate(self, xmlDoc):
		"""Create a volume based on the xml passed from the UI
		"""
		
		
		volumes = xmlDoc.findall('volume')
				
		cfg.LOGGER.info('%s Initiating vol create process for %d volume(s)', time.asctime(), len(volumes))

		rcSum = 0

		for volXML in volumes:
			volName = volXML.find('settings').attrib['name']
			cfg.CLUSTER.addVolume(volXML)
		
			# Look at the return code from the create process
			rc = cfg.CLUSTER.volume[volName].retCode
		
			if rc == 0:
				# Create volume was successful
				cfg.LOGGER.info("%s Volume creation was successful for '%s'", time.asctime(), volName)
				msg = "Gluster volume '%s' created successfully"%(volName) 
			else:
				# Problem creating the volume
				cfg.LOGGER.info("%s Create failed for volume '%s', rc=%d", time.asctime(), volName, rc)
				msg = "Gluster volume create failed for '%s'"%(volName)

			RequestHandler.taskLog.append(msg)
			print "\t\t" + msg
			
			rcSum += rc		# keep a running total of re codes, if 0 all is well!
		
		createMsg = 'OK' if rcSum == 0 else 'FAILED'
		
		response = "<response><status-text>" + createMsg + "</status-text></response>"
					
		RequestHandler.pollingEnabled = False			
		
		return response
		
	def __rqstFinish(self):
		"""Send the final summary of tasks done in the UI back to the 
		caller, to allow the build of the 'Finish' page
		"""
		
		cfg.LOGGER.debug("%s Sending results to the UI for display", time.asctime())
		
		response = "<response><tasksummary>"
		for taskInfo in RequestHandler.taskLog:
			response += "<message>" + taskInfo + "</message>"
		response += "</tasksummary></response>"		
		
		return response
		
	def __rqstQueryStatus(self):
		"""Return a list of messages on the current msg stack
		"""
		
		cfg.LOGGER.debug("%s query-status received from the web client", time.asctime())
		
		msgs = cfg.MSGSTACK.popMsgs()
		
		xmlMsgs = ""
		for msg in msgs:
			xmlMsgs += "<message>" + msg + "</message>"
		
		
		respText = "OK" if ( ( RequestHandler.pollingEnabled ) or ( len(msgs) > 0 ) ) else "NOTOK"
		response = ( "<response><status-text>" + respText + "</status-text>"
					+ xmlMsgs + "</response>")
		
		cfg.LOGGER.debug("%s query-status returned %s", time.asctime(), response)
			
		return response
		
	def __rqstGetPage(self, htmlFile, target):
		"""Receive the html file to load, and return that wrapped in xml
		to the caller
		"""
	
		return "<response>" + nextPageXML(htmlFile, target) + "</response>"
		

	def do_GET(self):
		"""Override get method, checking the client IP to prevent more than
		client IP connecting to the webserver at the same time
		"""
		
		thisIP = self.client_address[0]

		if RequestHandler.adminIP == '':
			RequestHandler.adminIP = thisIP
			cfg.LOGGER.info("%s Admin access to the interface is locked to %s", time.asctime(), thisIP)

		if thisIP != RequestHandler.adminIP:
			self.path = "/www/disallowed.html"
			cfg.LOGGER.info("%s Setup wizard access attempt from %s DENIED", time.asctime(), thisIP)

		return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

	def do_QUIT(self):
		"""Internal quit handler to terminate additional request threads """
		
		self.send_response(200)         # completed ok
		#self.end_headers()              # blank line end of http response
		self.server.stop=True
		self.finish()

		 
		 
	def do_POST(self):
		"""Handle the AJAX request looking at it's 'type' to determine the
		the appropriate __rqst* handler to invoke to define the response
		back to to the user
		"""
		
		self.daemon=True		
		

		length = int(self.headers.getheader('content-length'))        
		dataString = self.rfile.read(length)
		

		try:
			xmlRoot = ETree.fromstring(dataString)
			requestType = xmlRoot.find('./request-type').text
			
		except:
			print "XML parsing error - string received was " + dataString
			self.server.stop = True
			exit(8)
			return

		if requestType in RequestHandler.pollingEnabledTasks:
			cfg.LOGGER.debug("%s Message polling from the client is enabled for %s", time.asctime(),requestType)
			RequestHandler.pollingEnabled = True
		
		if ( requestType == "password" ):
			
			# Called from loginPage.js
		
			response = self.__rqstPassword(xmlRoot)
			self.sendResponse(response)
				
			
		elif ( requestType == "subnet-list" ):
			
			# Called from nodeDiscovery.js
			
			response = self.__rqstSubnetList()
			self.sendResponse(response)
			
		elif ( requestType == "find-nodes" ):
			
			# Called from nodeDiscovery.js
			
			response = self.__rqstFindNodes(xmlRoot)
			self.sendResponse(response)
			
		elif (requestType == "create-cluster"):

			# Called from nodeDiscovery.js

			response = self.__rqstCreateCluster(xmlRoot)
			self.sendResponse(response)
			
		elif ( requestType == "push-keys" ):

			# Called from keyMgmt.js
	
			response = self.__rqstPushKeys(xmlRoot)
			self.sendResponse(response)
			
		elif ( requestType == "find-disks" ):	
			
			# Called from diskDiscovery.js
			
			response = self.__rqstFindDisks()
			self.sendResponse(response)
			
		elif ( requestType == "register-bricks" ):

			# Called from diskDiscovery.js
			
			response = self.__rqstRegisterBricks(xmlRoot)
			self.sendResponse(response)
			
		elif ( requestType == "build-bricks" ):		
			
			# Called from brickDefinition.js
			
			response = self.__rqstBuildBricks(xmlRoot)
			self.sendResponse(response)
	
		elif ( requestType == "vol-create" ):
			
			# Called from volCreate.js
			
			response = self.__rqstVolCreate(xmlRoot)
			self.sendResponse(response)	

		elif (requestType == "finish"):
			
			# Called from finish.js
			
			response = self.__rqstFinish()
			self.sendResponse(response)

		elif (requestType == 'get-modal'):
			
			# called from any page that invokes a modal dialog
			
			page = xmlRoot.find('page-request')
			htmlFile = page.attrib['htmlfile']			# html page
		
			response = self.__rqstGetPage(htmlFile,'md-content')
			self.sendResponse(response)

		elif (requestType == "query-status"):
			
			# Called from layoutMgmt.js
			
			response = self.__rqstQueryStatus()
			self.sendResponse(response)
			
			self.request.close()

		
		elif ( requestType == "quit"):
			print "\t\tQuit received from the UI"
			
			# Update the httpd servers state, so the run forever loop can be exited
			self.server.stop = True
			self.dummyRequest()		# Send a dummy request to force thread termination
			self.finish()
			return
		
	def dummyRequest(self):
		""" Forces a dummy request to ensure thread termination """
	
		conn = httplib.HTTPConnection('localhost:%d'%(cfg.HTTPPORT))
		conn.request('QUIT','/')
		self.server.stop=True
		conn.getresponse()
		conn.close()
						

	def log_message(self, format, *args):
		""" Override std log_message method to record http messages only for debug mode """
			
		if cfg.LOGLEVEL == 10:				# 10 = DEBUG, 20=INFO, 30=WARN
			cfg.LOGGER.debug("%s %s %s", time.asctime(), self.address_string(), args)
		return


class StoppableHTTPServer (SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	"""Standard HTTPServer extended with a multi-threading and a 'Stop' 
		capability - SocketServer.ThreadingMixIn
	"""
	
	daemon_threads = True 	# Ensure ctrl-c kills all spawned threads
	
	def serve_forever(self):
		"""Overridden method to insert the stop process"""
		self.stop = False
		self.daemon=True	
		while not self.stop:
			self.handle_request()

		cfg.LOGGER.debug('%s http server serve_forever loop exited', time.asctime())

	
		


if __name__ == '__main__':
	pass

