#!/usr/bin/env python
#
#  network.py
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
#  Potential Substitutes - python-netifaces, python-netaddr
#
#
#

import sys
from syscalls import issueCMD 
import socket
import struct
import logging
import time

import globalvars as g

# glusterLog = logging.getLogger()

#VALIDPREFIX = ('eth', 'bond', 'em','virbr0','ovirtmgmt','rhevm')

def atod(a): # ascii_to_decimal
    return struct.unpack("!L",socket.inet_aton(a))[0]

def dtoa(d): # decimal_to_ascii
    return socket.inet_ntoa(struct.pack("!L", d))

def ntoDotted(mask):
    bits = 0xffffffff ^ (1 << 32 - mask) - 1
    return socket.inet_ntoa(struct.pack('>I', bits))

def listIPRange(subnet):
	""" receive x.x.x.x/nn subnet, and return all IP's on that subnet """
	excludedSuffixes = ('.0','.254','.255')
	subnetStart, mask = subnet.split('/')
	
	mask = int(mask)
	net = atod(subnetStart)
	
	IPList = []
	
	for host in (dtoa(net+n) for n in range(0, 1<<32-mask)):
		if not host.endswith(excludedSuffixes):
			IPList.append(host)
	
	g.LOGGER.debug('%s IP range for %s has %d addresses', time.asctime(), subnet, len(IPList))
	
	return IPList

def calcSubnet(subnet):
	""" receive an ip address / mask and return the start of the 
		subnet based on the mask """
		
	IP, mask = subnet.split('/')

	dotted = ntoDotted(int(mask))
	dIP = atod(IP)
	dmask = atod(dotted)
	
	return dtoa(dIP & dmask) + "/" + str(mask)
		

def findService(subnet, targetPort=24007,scanTimeout=0.05):
	""" Function that accepts a subnet as input in the form x.x.x.x/mask
		and then scans that subnet for a given target port.
		For every ip with that port open, attempt to resolve the IP - if
		not just use the IP.
	""" 
	
	excludedSuffixes = ('.0','.254','.255')
	
	mask = subnet.split('/')[-1]

	IPRange = listIPRange(subnet)	
	
	hostsIP = getHostIP()
	
	serviceList = []

	for IPaddr in IPRange:

		try:
			
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.settimeout(scanTimeout)
			
			result = sock.connect_ex((IPaddr,targetPort))
			if result == 0:
								
				g.LOGGER.debug('%s port %d found open on %s', time.asctime(),targetPort,IPaddr)
				
				# check if this IP is from this host - if so set suffix
				suffix = '*' if IPaddr in hostsIP else ''

				try:
					hostName = socket.gethostbyaddr(IPaddr)[0]
					
					# If the name returned is FQDN, just take the server name
					# component
					if '.' in hostName:
						hostName = hostName.split('.')[0]
						
					hostName += suffix
					
				except:
					hostName = IPaddr + suffix
					
				serviceList.append(hostName)
				
				# Add 'found host' message to the message stack
				g.MSGSTACK.pushMsg('Found %s' %(hostName))
				
			sock.close()
		except:
			pass
	
		
		
	return sorted(serviceList)

def getSubnets():
	"""getSubnets returns a list of the IPv4 subnets available of the host"""
	
	subnetList = []
	#validPrefix = ['eth', 'bond', 'em','virbr']
	ipInfo = issueCMD("ip addr show")
	
	for dataLine in ipInfo[1:]:
		if 'inet ' in dataLine:
			interface = dataLine.split()[-1]
			if interface.startswith(g.NICPREFIX):
				IPinfo = dataLine.split()[1]
				thisSubnet = calcSubnet(IPinfo)
				subnetList.append(thisSubnet)
	
	return subnetList

def getHostIP():
	"""	Get a list of IPs the host has defined """
	hostIP = []

	ipInfo = issueCMD("ip addr show")
	
	for dataLine in ipInfo[1:]:
		if 'inet ' in dataLine:
			interface = dataLine.split()[-1]
			if interface.startswith(g.NICPREFIX):
				dataLine = dataLine.replace('/',' ')
				hostIP.append(dataLine.split()[1])

	g.LOGGER.debug("%s Host has %s IP's to bind the web server to", time.asctime(), len(hostIP))


	return hostIP

if __name__ == "__main__":
	pass
	
