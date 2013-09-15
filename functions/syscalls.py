#!/usr/bin/env python

import subprocess 
import os
import random 
import string
import logging
import time
import pexpect

glusterLog = logging.getLogger()

class SSHsession:
	"""	SSH session class """
	
	def __init__(self, user, host, password=None):
		""" Establish ssh session properties """
		self.user = user
		self.host = host
		self.password = password
		
		# responses determines the events that are managed by the __exec method
		self.responses=['Are you sure you want to continue connecting', 
						'[pP]assword:', 
						'@@@@@@@@@@@@',
						pexpect.EOF]
		pass
		
	def ssh(self, command):
		""" run a standard ssh with a single command """
		return self.__exec("ssh -l %s %s %s" % (self.user,self.host,command))
	
	def sshScript(self,scriptName):
		""" Execute a bash script on the remote machine """
		
		if os.path.exists(scriptName):
		
			command = """/bin/bash -c "/usr/bin/ssh  %s@%s 'bash -s' < %s" """ % (self.user, self.host, scriptName)
			response = self.__exec(command)
		else:
			glusterLog.debug('%s script provided to SSHsession.sshScript can not be found', time.asctime())
			response = ['ERROR-SCRIPT-NOT-FOUND']

		return response

	def sshPython(self,scriptName):
		""" Execute a local python script on the remote machine """
		
		if os.path.exists(scriptName):
		
			command = """/bin/bash -c "/usr/bin/ssh  %s@%s 'python' < %s" """ % (self.user, self.host, scriptName)
			response = self.__exec(command)
		else:
			glusterLog.debug('%s script provided to SSHsession.sshPython can not be found', time.asctime())
			response = ['ERROR-SCRIPT-NOT-FOUND']

		return response
		
	
	def sshCopyID(self):
		""" handle the ssh-copy-id process """
		
		keyFile = os.path.expanduser('~') + '/.ssh/id_rsa.pub'
		cmd = 'ssh-copy-id -i ' + keyFile + ' ' + self.user + '@' + self.host
		rc = 0
		cmdOut = self.__exec(cmd)
		
		# check for permission denied response - i.e. bad password
		if 'Permission' in cmdOut[1]:
			glusterLog.debug('%s ssh key not added due to bad password for node %s', time.asctime(), self.host)
			rc = 8
			
		# /usr/bin/ssh-copy-id: WARNING: All keys were skipped because they already exist
		elif 'keys were skipped' in cmdOut[2]:
			glusterLog.debug('%s ssh key already exists in %s authorized_keys file', time.asctime(), self.host)
			rc = 1
			
		else:
			glusterLog.debug('%s ssh key added to %s', time.asctime(), self.host)
			
			 
		return rc 
		
	def __repr__(self):
		"""	Display the object's attribute info """
		
		objInfo = 'Class :'+self.__class__.__name__
		for attr in self.__dict__:
			if attr == 'password':
				objInfo += '\n\t'+attr+' : '+'*'*len(self.password)
			else:
				objInfo += '\n\t'+attr+' : '+str(getattr(self, attr))
		return objInfo
		
	
	def __exec(self,command):
		""" 
			Execute the given command string and handle the ssh interaction 
			The returned output is a list in unicode format
		"""
		
		child = pexpect.spawn(command, timeout=30)	# 30 sec timeout
		ptr = child.expect(self.responses)
		if ptr == 0:
			# first time connecting
			child.sendline('yes')
			i = child.expect(['[pP]assword:',pexpect.EOF])
			
			if i == 0:
				# send the password
				child.sendline(self.password)
				child.expect(pexpect.EOF)
				
		elif ptr == 1:
			child.sendline(self.password)
			
			i = child.expect(['[dD]enied',pexpect.EOF])
			if i == 0:
				# wrong password given
				child.close(True)
		
		elif ptr == 2:
			# key change detected - man in the middle error mesage
			glusterLog.debug('%s ssh login with %s to %s failed - Conflict in known_hosts file', time.asctime(), self.user, self.host)
			return ['ERROR-HOSTID-CHANGED']
			
		elif ptr == 3:
			# connect timeout!
			glusterLog.debug('%s Connection timeout in SSHsession.__exec %s@%s', time.asctime(), self.user, self.host)
			pass

		return child.before.split('\n')


def issueCMD(command):
	""" issueCMD takes a command to issue to the host and returns the response
		as a list
	"""

	cmdWords = command.split()
	try:
		out = subprocess.Popen(cmdWords,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(response, errors)=out.communicate()				# Get the output...response is a byte
	except Exception:
		response = 'command failed\n'						# string that includes \n
	
	return response.split('\n')								# use split to return a list	
	

def generateKey(length=26, charsAvailable=string.letters + string.digits):

	""" generateKey builds a 'length' character string of random characters
		suitable for one off passwords etc.
	"""
	
	key = ''.join([random.choice(charsAvailable) for n in range(length)])
	glusterLog.debug('%s Access key generated was %s', time.asctime(), key)
		
	return key


def distributeKeys(keyState, keyData):
	"""	receive a progress task containing the nodes to act upon, and the data from the
		web in the form nodename*password<space> repeated
	"""
	
	for nodeData in keyData:
		(nodeName, nodePassword) = nodeData.split('*')
		
		keyState.targetList.remove(nodeName)
		
		sshTarget = SSHsession('root', nodeName, nodePassword)
		copyRC = sshTarget.sshCopyID()
		
		if copyRC <= 4:
			keyState.successList.append(nodeName)
			glusterLog.info('%s ssh key added successfully to %s', time.asctime(), nodeName)
		else:
			keyState.failureList.append(nodeName)
			glusterLog.info('%s Adding ssh key to %s failed', time.asctime(), nodeName)


if __name__ == "__main__":
	print "Testing function with 26 character key"
	print "--> " + generateKey(26);
