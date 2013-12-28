#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  btrfsQuota.py
#  
#  Copyright 2013 Paul <paul.cuzner@redhat.com>
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

# Based on code available from https://btrfs.wiki.kernel.org/index.php/Quota_support
# Modified to use Popen function, with some reformatting and validation testing

import argparse				# command line option parsing
import subprocess
import shlex


def issueCMD(command, shellNeeded=False):
	""" issueCMD takes a command to issue to the host and returns the response as a list """

	if shellNeeded:
		args =command
	else:
		args = shlex.split(command)

	try:
		child = subprocess.Popen(args,shell=shellNeeded,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		
		# Get output...response is a byte string that includes \n		
		(response, errors)=child.communicate()
		rc = child.returncode	 

	except Exception:
		response = 'command failed\n' 
		rc=12

	cmdText = response.split('\n')[:-1]
	
	return (rc, cmdText)                 


def main(units,mount_point):
	print "\nChecking " + mount_point
	
	multiplicator_lookup = ['B', 'K', 'M', 'G', 'T', 'P']
	
	subvolume_data = dict()
	
	cmd = "btrfs subvolume list " + mount_point
	subvol_list = issueCMD(cmd)[1]
	
	# If we don't have any output, the mountpoint provided is not a btrfs filesystem
	if not subvol_list:
		
		print "-> Mount point provided (" + sys_args.mount_point + ") is not a btrfs filesystem"
		
	else:
		# subvolume command returned some output, so 1st create a lookup index
		for line in subvol_list:
			args = line.strip().split(' ')
			subvolume_data[int(args[1])] = args[-1]

		# Setup up the output headings
		print("Subvolume Name\t\t\t\t\tgroup         total    unshared")
		print("-" * 79)
		
		# Query the quota groups
		cmd = "btrfs qgroup show " + mount_point
		
		for line in issueCMD(cmd)[1][2:]:
			args = line.strip().split()
		
			try:
				subvolume_id = args[0].split('/')[-1]
				subvolume_name = subvolume_data[int(subvolume_id)]
			except:
				subvolume_name = "(unknown/root)"
		
			multiplicator = 1024 ** multiplicator_lookup.index(units)
		
			try:
				total = "%02.2f" % (float(args[1]) / multiplicator)
				unshared = "%02.2f" % (float(args[2]) / multiplicator)
		
				print("%s\t%s\t%s%s %s%s" % (
						subvolume_name.ljust(40),
						args[0],
						total.rjust(10), units,
						unshared.rjust(10), units,
						))
			except IndexError:
				pass
		
		print "\n"
	
	
if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(
				description='Gives quotas from a BTRFS filesystem in a readable form'
			 )
	parser.add_argument(
				'-u', '--unit', metavar='U', type=str,
				default='G',
				help='SI Unit, [B]ytes, K, M, G, T, P',
			 )
	parser.add_argument(
				'mount_point', metavar='PATH', type=str,
				default='/',
				help="BTRFS mount point (default is '/')",
			 )
			 
	sys_args = parser.parse_args()
	
	main(sys_args.unit.upper(), sys_args.mount_point)
