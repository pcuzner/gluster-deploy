#!/usr/bin/env python

import subprocess 
import os
import random 
import string
import logging
import time
import pexpect
import shlex

import globalvars as g 

# glusterLog = logging.getLogger()

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
						pexpect.EOF,
						pexpect.TIMEOUT]
		pass
		
	def ssh(self, command):
		""" run a standard ssh with a single command """
		return self.__exec("ssh -l %s %s %s" % (self.user,self.host,command))
	
	def sshScript(self,scriptName):
		""" 
		Execute a bash script on the remote machine, returning a list
		1st element is the return code
		nth element is the text of the output 
		"""
			
		response =[]
		
		scriptPath=scriptName.split(" ")[0]
		
		if os.path.exists(scriptPath):
			# The -- is critical to stop bash from claiming any parameter string passed to the script
			command = """/bin/bash -c "/usr/bin/ssh  %s@%s 'bash -s' -- < %s" """ % (self.user, self.host, scriptName)
			
			output = self.__exec(command)
			for line in output:
				if isinstance(line,basestring):
					if line > '':
						response.append(line.replace('\r',''))
				else:
					response.append(line)
		else:
			g.LOGGER.debug('%s script provided to SSHsession.sshScript can not be found', time.asctime())
			response = [16,'ERROR-SCRIPT-NOT-FOUND']

		return response

	def sshPython(self,scriptName):
		""" 
		Execute a local python script on the remote machine 
		- 1st element is the return code
		- nth element is the text of the output 
		"""
		response =[]
		
		if os.path.exists(scriptName):
		
			command = """/bin/bash -c "/usr/bin/ssh  %s@%s 'python' < %s" """ % (self.user, self.host, scriptName)
			
			output = self.__exec(command)
			for line in output:
				if isinstance(line,basestring):
					if line > '':
						response.append(line.replace('\r',''))
				else:
					response.append(line)
		else:
			g.LOGGER.debug('%s script provided to SSHsession.sshPython can not be found', time.asctime())
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
			g.LOGGER.debug('%s ssh key not added due to bad password for node %s', time.asctime(), self.host)
			rc = 8

		# Error host-id changed - previous key for this host no longer matches
		elif 'ERROR-HOSTID-CHANGED' in cmdOut[1]:
			rc = 8
			g.LOGGER.debug('%s ssh key in local known_hosts mismatch with target node (%s)', time.asctime(),self.host)
			
		# /usr/bin/ssh-copy-id: WARNING: All keys were skipped because they already exist
		elif 'keys were skipped' in cmdOut[2]:
			g.LOGGER.debug('%s ssh key already exists in %s authorized_keys file', time.asctime(), self.host)
			rc = 1
			
		else:
			g.LOGGER.debug('%s ssh key added to %s', time.asctime(), self.host)
			
			 
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
			g.LOGGER.debug('%s ssh login with %s to %s failed - Conflict in known_hosts file', time.asctime(), self.user, self.host)
			return [12,'ERROR-HOSTID-CHANGED']
			
		elif ptr == 3:
			# Child process exited
			child.close()
			g.LOGGER.debug('%s Child process to %s exited with %s', time.asctime(), self.host,str(child.exitstatus))
			pass

		response = [child.exitstatus] + child.before.split('\n')
		
		return response


def issueCMD(command, shellNeeded=False):
	""" issueCMD takes a command to issue to the host and returns the response as a list """

	if shellNeeded:
		args =command
	else:
		args = shlex.split(command)

	try:
		child = subprocess.Popen(args,shell=shellNeeded,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(response, errors)=child.communicate()	 # Get output...response is a byte string that includes \n
	except Exception:
		response = 'command failed\n' 

	cmdText = response.split('\n')[:-1]
	
	retList = [child.returncode] + cmdText				# Merge the lists together - [0] = RC	

	return retList                 # use split to return a list, skipping the last null entry



def generateKey(length=26, charsAvailable=string.letters + string.digits):

	""" 
	generateKey builds a 'length' character string of random characters
	suitable for one off passwords etc.
	"""
	
	key = ''.join([random.choice(charsAvailable) for n in range(length)])
	g.LOGGER.info('%s Access key generated was %s', time.asctime(), key)
		
	return key




if __name__ == "__main__":
	print "Testing function with 26 character key"
	print "--> " + generateKey(26);
