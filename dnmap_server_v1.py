#! /usr/bin/env python
#  Copyright (C) 2009  Sebastian Garcia
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
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Author:
# Sebastian Garcia eldraco@gmail.com
#
# Based on code from Twisted examples.
# Copyright (c) Twisted Matrix Laboratories.
#
# CHANGELOG
# 0.6
#  - Verify that the server.pem file exists
#
#
# TODO
# - If the client is processing a command and the servers goes down, do we lost that command!
# - Client authentication / registration?
# - Add libraries dependecy list
# - Sort the stats by some field
# - Put colors to the list
# - Show the ETA
# - Show progress status
#
import subprocess
import thread
from time import sleep
import logging
import logging.handlers
import datetime
import sys
# import sqlite3
# import os
# import xml.etree.ElementTree as ET

try:
	from twisted.internet.protocol import Factory, Protocol
	from twisted.internet import ssl, reactor, task
	from twisted.python import log
	from twisted.python.logfile import DailyLogFile
except:
	print 'You need twisted library. apt-get install python-twisted-bin python-twisted-core'
	exit(-1)

import getopt, sys, time, os
try:
	from OpenSSL import SSL
except:
	print 'You need python openssl library. apt-get install python-openssl'
	exit(-1)



##global variable from inions

vernum='0.6'
nmap_commands_file = ''
nmap_command = []
nmap_commands_sent = []
trace_file = ''
nmap_output_coming_back = False
XML_file= ''
GNmap_file=''
outputswitch=''
file_position = 0
clients = {}
port=46001
clientes = {}
base_dir = os.path.dirname(os.path.abspath(__file__))
#output_file=os.path.join(base_dir,"current_output")
log_file=os.path.join(base_dir, "log")
log_level='info'

###
# Global variables
#vernum='0.6'
#nmap_commands_file = ''
#nmap_command = []
#nmap_commands_sent = []
file_descriptor = ''
#trace_file = ''
#base_dir = os.path.dirname(os.path.abspath(__file__))
#nmap_output_coming_back = False
#output_file_descriptor = ''
#file_position = 0
#clients = {}
#port=46001
#log_file='/var/log/dnmap_server.log'
#log_level='info'
#clientes = {}
verbose_level = 2
	# 0: quiet
	# 1: info, normal
	# 2: Statistical table
	# 3: debug
	# 4: ?
	# 5: ?

# This is to assure that the first time we run, something is shown
temp = datetime.datetime.now()
delta = datetime.timedelta(seconds=5)
last_show_time = temp - delta

# defaults to 1 hour
client_timeout = 3600 

sort_type = 'Status'

# By default in the same directory
pemfile = '/usr/share/dnmap/server.pem'
# End of global variables


# Print version information and exit
def version():
  print "+----------------------------------------------------------------------+"
  print "| dnmap_server Version "+ vernum +"                                             |"
  print "| This program is free software; you can redistribute it and/or modify |"
  print "| it under the terms of the GNU General Public License as published by |"
  print "| the Free Software Foundation; either version 2 of the License, or    |"
  print "| (at your option) any later version.                                  |"
  print "|                                                                      |"
  print "| Author: Garcia Sebastian, eldraco@gmail.com                          |"
  print "| www.mateslab.com.ar                                                  |"
  print "+----------------------------------------------------------------------+"
  print


# Print help information and exit:
def usage():
  print "+----------------------------------------------------------------------+"
  print "| dnmap_server Version "+ vernum +"                                             |"
  print "| This program is free software; you can redistribute it and/or modify |"
  print "| it under the terms of the GNU General Public License as published by |"
  print "| the Free Software Foundation; either version 2 of the License, or    |"
  print "| (at your option) any later version.                                  |"
  print "|                                                                      |"
  print "| Author: Garcia Sebastian, eldraco@gmail.com                          |"
  print "| www.mateslab.com.ar                                                  |"
  print "+----------------------------------------------------------------------+"
  print "\nusage: %s <options>" % sys.argv[0]
  print "options:"
  print "  -f, --nmap-commands        Nmap commands file"
  print "  -p, --port        TCP port where we listen for connections."
  print "  -L, --log-file        Log file. Defaults to /var/log/dnmap_server.conf."
  print "  -l, --log-level       Log level. Defaults to info."
  print "  -v, --verbose_level         Verbose level. Give a number between 1 and 5. Defaults to 1. Level 0 means be quiet."
  print "  -t, --client-timeout         How many time should we wait before marking a client Offline. We still remember its values just in case it cames back."
  print "  -s, --sort         	Field to sort the statical value. You can choose from: Alias, #Commands, UpTime, RunCmdXMin, AvrCmdXMin, Status"
  print "  -P, --pem-file         pem file to use for TLS connection. By default we use the server.pem file provided with the server in the current directory."
  print
  print "dnmap_server uses a \'<nmap-commands-file-name>.dnmaptrace\' file to know where it must continue reading the nmap commands file. If you want to start over again,"
  print "just delete the \'<nmap-commands-file-name>.dnmaptrace\' file"
  print
  sys.exit(1)


def timeout_idle_clients():
	"""
	This function search for idle clients and mark them as offline, so we do not display them
	"""
	global mlog
	global verbose_level
	global clients
	global client_timeout
	try:

		for client_id in clients:
			now = datetime.datetime.now()
			time_diff = now - clients[client_id]['LastTime']
			if time_diff.seconds >= client_timeout:
				clients[client_id]['Status']='Offline'


	except Exception as inst:
		if verbose_level > 2:
			msgline = 'Problem in mark_as_idle function'
			mlog.error(msgline)
			print msgline
			msgline = type(inst)
			mlog.error(msgline)
			print msgline
			msgline = inst.args
			mlog.error(msgline)
			print msgline
			msgline = inst
			mlog.error(msgline)
			print msgline



def read_file_and_fill_nmap_variable():
	""" Here we fill the nmap_command with the lines of the txt file. Only the first time. Later this file should be filled automatically"""
	global nmap_commands_file
	global nmap_command
	global file_descriptor
	global trace_file
	global file_position
	global mlog
	global verbose_level

	with open(nmap_commands_file,'r') as f:
		jobs = f.readlines()
	if not file_descriptor:
		file_descriptor = open(nmap_commands_file,'r')

	last_line = ''
	#if not trace_file_descriptor:
	trace_file = nmap_commands_file+'.dnmaptrace'

	try:
		size = os.stat(trace_file).st_size
		trace_file_descriptor = open(trace_file,'r')
		if size > 0:
			# We already have a trace file. We must be reading the same original file again after some running...
			trace_file_descriptor.seek(0)
			last_line = trace_file_descriptor.readline()
			
			# Search for the line stored in the trace file
			# This allow us to CTRL-C the server and reload it again without having to worry about were where we reading commnds...
			otherline = file_descriptor.readline()
			while otherline:
				if last_line == otherline:
					break
				otherline = file_descriptor.readline()
		trace_file_descriptor.close()

	except OSError:
		pass

	# Do we have some more lines added since last time?
	if file_position != 0:
		# If we are called again, and the file was already read. Close the file so we can 'see' the new commands added
		# and then continue from the last previous line...
		file_descriptor.flush()
		file_descriptor.close()
		file_descriptor = open(nmap_commands_file,'r')

		# Go forward until what we read last time
		file_descriptor.seek(file_position)

	line = file_descriptor.readline()
	file_position = file_descriptor.tell()
	lines_read = 0
	while line:
		# Avoid lines with # so we can comment on them
		if not '#' in line:
			nmap_command.insert(0,line)
		line = file_descriptor.readline()
		file_position = file_descriptor.tell()
		lines_read += 1
	

	msgline = 'Command lines read: {0}'.format(lines_read)
	mlog.debug(msgline)
	
	return




class ServerContextFactory:
	global mlog
	global verbose_level
	global pemfile
	# Copyright (c) Twisted Matrix Laboratories.
	""" Only to set up SSL"""
	def getContext(self):
		"""
		Create an SSL context.
		This is a sample implementation that loads a certificate from a file 
		called 'server.pem'.
		The file server.pem was copied from apache!
		"""
		ctx = SSL.Context(SSL.SSLv23_METHOD)
		try:
			ctx.use_certificate_file(pemfile)
			ctx.use_privatekey_file(pemfile)
		except:
			print 'You need to have a server.pem file for the server to work. If it is not in your same directory, just point to it with -P parameter'
		return ctx



def show_info():
	global verbose_level
	global mlog
	global clients
	global last_show_time
	global start_time
	global sort_type

	try:
		now = datetime.datetime.now()
		diff_time = now - start_time

		amount = 0
		for j in clients:
			if clients[j]['Status'] != 'Offline':
				amount += 1

		if verbose_level > 0:
			line = '=| MET:{0} | (Roy-MyVersion1.2)Amount of Online clients: {1} |='.format(diff_time, amount) + "commands left to execute:" + str(len(nmap_command))
			print line
			#print len(nmap_command)
			mlog.info(line)

		if clients != {}:
			if verbose_level > 1:
				line = 'Clients connected'
				print line
				mlog.info(line)
				line = '-----------------'
				print line
				mlog.info(line)
				#line = 'Alias\t#Commands\tLast Time Seen\t\t\tVersion\tIsRoot\tStatus'
				line = '{0:15}\t{1}\t{2}\t{3}\t{4}\t\t{5}\t{6}\t{7}\t{8}\t{9}'.format('Alias','#Commands','Last Time Seen', '(time ago)', 'UpTime', 'Version', 'IsRoot', 'RunCmdXMin', 'AvrCmdXMin', 'Status')
				print line
				mlog.info(line)
				for i in clients:
					if clients[i]['Status'] != 'Offline':
						# Strip the name of the day and the year
						temp = clients[i]['LastTime'].ctime().split(' ')[1:-1]
						lasttime = ''
						for j in temp:
							lasttime = lasttime + str(j) + ' '

						time_diff = datetime.datetime.now() - clients[i]['LastTime']
						#time_diff_secs = int(time_diff.total_seconds() % 60)
						#time_diff_secs = int(time_diff.seconds % 60)
						time_diff_secs = int( (time_diff.seconds + (time_diff.microseconds / 1000000.0) ) % 60)
						#time_diff_mins = int(time_diff.total_seconds() / 60)
						#time_diff_mins = int(time_diff.seconds / 60)
						time_diff_mins = int(  (time_diff.seconds + (time_diff.microseconds / 1000000.0) ) / 60)
						uptime_diff = datetime.datetime.now() - clients[i]['FirstTime']
						#uptime_diff_hours = int(uptime_diff.total_seconds() / 3600)
						#uptime_diff_hours = int(uptime_diff.seconds / 3600)
						uptime_diff_hours = int( (uptime_diff.seconds + (uptime_diff.microseconds / 1000000.0)) / 3600)
						#uptime_diff_mins = int(uptime_diff.total_seconds() % 3600 / 60)
						#uptime_diff_mins = int(uptime_diff.seconds % 3600 / 60)
						uptime_diff_mins = int( ((uptime_diff.seconds % 3600) + (uptime_diff.microseconds / 1000000.0)) / 60)

						line = '{0:15}\t{1}\t\t{2}({3:2d}\'{4:2d}\")\t{5:2d}h{6:2d}m\t\t{7}\t{8}\t{9:10.1f}\t{10:9.1f}\t{11}'.format(clients[i]['Alias'], clients[i]['NbrCommands'], lasttime, time_diff_mins, time_diff_secs, uptime_diff_hours, uptime_diff_mins , clients[i]['Version'], clients[i]['IsRoot'], clients[i]['RunCmdsxMin'], clients[i]['AvrCmdsxMin'], clients[i]['Status'])
						print line
						mlog.info(line)

			print
			last_show_time = datetime.datetime.now()

	except Exception as inst:
		if verbose_level > 2:
			msgline = 'Problem in show_info function'
			mlog.error(msgline)
			print msgline
			msgline = type(inst)
			mlog.error(msgline)
			print msgline
			msgline = inst.args
			mlog.error(msgline)
			print msgline
			msgline = inst
			mlog.error(msgline)
			print msgline
	


def send_one_more_command(ourtransport,client_id):
	# Extract the next command to send.
	global nmap_command
	global verbose_level
	global mlog
	global clients

	try:
		alias = clients[client_id]['Alias']

		command_to_send = nmap_command.pop()

		line = 'Data sent to client ID '+client_id+' ('+alias+')'
		log.msg(line, logLevel=logging.INFO)
		if verbose_level > 2:
			print line
		line= '\t'+command_to_send.strip('\n')
		log.msg(line, logLevel=logging.INFO)
		if verbose_level > 2:
			print line
		ourtransport.transport.write(command_to_send)
		clients[client_id]['NbrCommands'] += 1
		clients[client_id]['LastCommand'] = command_to_send
		clients[client_id]['Status'] = 'Executing'


	except IndexError:
		# If the list of commands is empty, look for new commands
		line = 'No more commands in queue - Roy .' + str(len(nmap_command))
		# print len(nmap_command)
		# print "no more commands - len is finished"
		try:
			os.mknod("dnmap.finished")
		except OSError:
			print "FileExists"
		# print len(nmap_command)
		# # try:
		# if len(nmap_command) == 0:
		# 	print 'no more commands in commands file - exiting'
		# sleep(120)
		# 	read_file_and_fill_nmap_variable()
		# 	thread.interrupt_main()
		# sys.exit('no more commands in commands file - exitin

		log.msg(line, logLevel=logging.DEBUG)
		if verbose_level > 2:
			print line
		line = '\tMaking the client '+str(client_id)+' ('+str(alias)+')'+' wait 10 secs for new commands to arrive...'
		log.msg(line, logLevel=logging.DEBUG)
		if verbose_level > 2:
			print line
		ourtransport.transport.write('Wait:10')
		# print "waiting for 35 seconds before shutting down dnmapserver due to end of commands(indexError)"
		# sleep(35)
		# thread.interrupt_main()
	except Exception as inst:
		print 'Problem in Send More Commands'
		print type(inst)
		print inst.args
		print inst
		print "waiting for 35 seconds before shutting down dnmapserver due to end of commands"
		sleep(35)
		thread.interrupt_main()


def process_input_line(data,ourtransport,client_id):
	global mlog
	global verbose_level
	global clients
	global trace_file
	global nmap_command
	global nmap_output_coming_back
	global nmap_output_file
	global xml_output_file
	global gnmap_output_file
	global outputswitch
	try:
		# What to do. Send another command or store the nmap output?
		if 'Starts the Client ID:' in data:
			# No more nmap lines coming back
			if nmap_output_coming_back:
				nmap_output_coming_back = False

			alias = data.split(':')[3].strip('\n').strip('\r').strip(' ')
			try:
				client_version = data.split(':')[5].strip('\n').strip('\r').strip(' ')
				client_isroot = 'False' if data.split(':')[7].strip('\n').strip('\r').strip(' ') == 0 else 'True'
			except IndexError:
				# It is an old version and it is not sending these data
				client_version = '0.1?'
				client_isroot = '?'

			try:
				# Do we have it yet?
				value = clients[client_id]['Alias']
				# Yes
			except KeyError:
				# No
				clients[client_id] = {}
				clients[client_id]['Alias'] = alias
				clients[client_id]['FirstTime'] = datetime.datetime.now()
				clients[client_id]['LastTime'] = datetime.datetime.now()
				clients[client_id]['NbrCommands'] = 0
				clients[client_id]['Status'] = 'Online'
				clients[client_id]['LastCommand'] = ''
				clients[client_id]['Version'] = client_version
				clients[client_id]['IsRoot'] = client_isroot
				clients[client_id]['RunCmdsxMin'] = 0
				clients[client_id]['AvrCmdsxMin'] = 0

			msgline = 'Client ID connected: {0} ({1})'.format(str(client_id),str(alias))
			log.msg(msgline, logLevel=logging.INFO)
			if verbose_level > 1:
				print '+ '+msgline

		elif 'Send more commands' in data:
			alias = clients[client_id]['Alias']
			
			clients[client_id]['Status'] = 'Online'
			#nowtime = datetime.datetime.now().ctime()
			nowtime = datetime.datetime.now()
			clients[client_id]['LastTime'] = nowtime

			# No more nmap lines coming back
			if nmap_output_coming_back:
				nmap_output_coming_back = False

			send_one_more_command(ourtransport,client_id)


		elif 'Nmap Output File' in data and not nmap_output_coming_back:
			# Nmap output start to come back...
			nmap_output_coming_back = True
			outputswitch=0
			alias = clients[client_id]['Alias']


			clients[client_id]['Status'] = 'Online'

			# compute the commands per hour
			# 1 more command. Time is between lasttimeseen and now
			time_since_cmd_start = datetime.datetime.now() - clients[client_id]['LastTime']

			# Cummulative average
			prev_ca = clients[client_id]['AvrCmdsxMin']
			#commandsXsec = ( time_since_cmd_start.total_seconds() + (clients[client_id]['NbrCommands'] * prev_ca) ) / ( clients[client_id]['NbrCommands'] + 1 )
			#clients[client_id]['RunCmdsxMin'] =  cmds_per_min = 60 / time_since_cmd_start.total_seconds()
			clients[client_id]['RunCmdsxMin'] =  60 / ( time_since_cmd_start.seconds + ( time_since_cmd_start.microseconds / 1000000.0))
			
			clients[client_id]['AvrCmdsxMin'] = ( clients[client_id]['RunCmdsxMin'] + (clients[client_id]['NbrCommands'] * prev_ca) ) / ( clients[client_id]['NbrCommands'] + 1 )

			# update the lasttime
			nowtime = datetime.datetime.now()
			clients[client_id]['LastTime'] = nowtime


			# Create the dir
			os.system('mkdir %s/nmap_results > /dev/null 2>&1'%base_dir)

			# Get the output file from the data
			# We strip \n. 
			filename = data.split(':')[1].strip('\n')
			xml_output_file = "%s/nmap_results/%s.xml"%(base_dir, filename)
			nmap_output_file = "%s/nmap_results/%s.nmap"%(base_dir, filename)
			gnmap_output_file = "%s/nmap_results/%s.gnmap"%(base_dir, filename)
			if verbose_level > 2:
				log.msg('\tNmap output file is: {0}'.format(nmap_output_file), logLevel=logging.DEBUG)

			# clientline = 'Client ID:'+client_id+':Alias:'+alias+"\n"
			# with open(nmap_output_file, 'a+') as f:
			# 	f.writelines(clientline)
			# with open(xml_output_file, 'a+') as f:
			# 	f.writelines(clientline)
			# with open(gnmap_output_file, 'a+') as f:
			# 	f.writelines(clientline)

		elif nmap_output_coming_back and 'Nmap Output Finished' not in data:
			# Store the output to a file.
			alias = clients[client_id]['Alias']
			clients[client_id]['Status'] = 'Storing'
			#nowtime = datetime.datetime.now().ctime()
			nowtime = datetime.datetime.now()
			clients[client_id]['LastTime'] = nowtime
			#print data
			if "#XMLOUTPUT#" in data:
				outputswitch=1
				
			elif "#GNMAPOUTPUT#" in data:
				outputswitch=2
				
			else:
				if outputswitch==0:
					with open(nmap_output_file, 'w') as f:
						f.writelines(data+'\n')
					
				elif outputswitch==1:
					with open(xml_output_file, 'w') as f:
						f.writelines(data+'\n')
					
				elif outputswitch==2:
					with open(gnmap_output_file, 'w') as f:
						f.writelines(data+'\n')
					

			log.msg('\tStoring nmap output for client {0} ({1}).'.format(client_id, alias), logLevel=logging.DEBUG)


				
		elif 'Nmap Output Finished' in data and nmap_output_coming_back:
			# Nmap output finished
			nmap_output_coming_back = False

			alias = clients[client_id]['Alias']

			clients[client_id]['Status'] = 'Online'
			#nowtime = datetime.datetime.now().ctime()
			nowtime = datetime.datetime.now()
			clients[client_id]['LastTime'] = nowtime
		
			# Store the finished nmap command in the file, so we can retrieve it if we need...
			finished_nmap_command = clients[client_id]['LastCommand']
			clients[client_id]['LastCommand'] = ''

			# #clear out the trace file
			# with open(trace_file, 'r') as f:
			# 	running_jobs = f.readlines()
			# running_jobs.remove(finished_nmap_command)
			# with open(trace_file, 'w') as f:
			# 	f.writelines(running_jobs)
			# Store the finished nmap command in the file, so we can retrieve it if we need...

			trace_file = nmap_commands_file + '.dnmaptrace'
			# finished_nmap_command = clients[client_id]['LastCommand']
			trace_file_descriptor = open(trace_file, 'w')
			trace_file_descriptor.seek(0)
			trace_file_descriptor.writelines(finished_nmap_command)
			trace_file_descriptor.flush()
			trace_file_descriptor.close()


			if verbose_level > 2:
				print '+ Storing command {0} in trace file.'.format(finished_nmap_command.strip('\n').strip('\r'))
			outputswitch=0

	except Exception as inst:
		print 'Problem in process input lines'
		print type(inst)
		print inst.args
		print inst

class NmapServerProtocol(Protocol):
	""" This is the function that communicates with the client """
	global mlog
	global verbose_level
	global clients
	global nmap_command
	global mlog

	def connectionMade(self):
		if verbose_level > 0:
			pass

	def connectionLost(self, reason):
		peerHost = self.transport.getPeer().host
		peerPort = str(self.transport.getPeer().port)
		client_id = peerHost+':'+peerPort
		alias = clients[client_id]['Alias']

		if verbose_level > 1:
			msgline = 'Connection lost in the protocol. Reason:{0}'.format(reason)
			msgline2 = '+ Connection lost for {0} ({1}).'.format(alias, client_id)
			log.msg(msgline, logLevel=logging.DEBUG)
			print msgline2

			clients[client_id]['Status'] = 'Offline'
			command_to_redo = clients[client_id]['LastCommand']
			if command_to_redo != '':
				nmap_command.append(command_to_redo)
			if verbose_level > 2:
				print 'Re inserting command: {0}'.format(command_to_redo)


	def dataReceived(self, newdata):
		#global client_id

		data = newdata.strip('\r').strip('\n').split('\r\n')

		peerHost = self.transport.getPeer().host
		peerPort = str(self.transport.getPeer().port)
		client_id = peerHost+':'+peerPort

		# If you need to debug
		if verbose_level > 2:
			log.msg('Data recived', logLevel=logging.DEBUG)
			log.msg(data, logLevel=logging.DEBUG)
			print '+ Data received: {0}'.format(data)

		for line in data:
			process_input_line(line,self,client_id)







def process_nmap_commands(logger_name):
	""" Main function. Here we set up the environment, factory and port """
	global nmap_commands_file
	global nmap_command
	global port
	global mlog
	global verbose_level
	global client_timeout

	observer = log.PythonLoggingObserver(logger_name)
	observer.start()

	# Create the factory
	factory = Factory()
	factory.protocol = NmapServerProtocol

	# Create the time based print
	loop = task.LoopingCall(show_info)
	loop.start(5.0) # call every second

	# Create the time based file read
	loop2 = task.LoopingCall(read_file_and_fill_nmap_variable)
	loop2.start(30.0) # call every second

	# To mark idel clients as hold
	loop3 = task.LoopingCall(timeout_idle_clients)
	loop3.start(client_timeout) # call every second

	# Create the reactor
	reactor.listenSSL(port, factory, ServerContextFactory())
	reactor.run()




def main():
	global nmap_commands_file
	global port
	global log_file
	global log_level
	global mlog
	global verbose_level
	global start_time
	global client_timeout
	global sort_type
	global pemfile

	start_time = datetime.datetime.now()

	try:
		opts, args = getopt.getopt(sys.argv[1:], "f:l:L:p:P:s:t:v:", ["nmap-commands=","log-level=","log-server=","port=","pem-file=", "sort-type=","client-timeout=","verbose-level="])
	except getopt.GetoptError: usage()

	for opt, arg in opts:
	    if opt in ("-f", "--nmap-commands"): nmap_commands_file=str(arg)
	    if opt in ("-p", "--port"): port=int(arg)
	    if opt in ("-l", "--log-level"): log_level=arg
	    if opt in ("-L", "--log-file"): log_file=arg
	    if opt in ("-v", "--verbose-level"): verbose_level=int(arg)
	    if opt in ("-t", "--client-timeout"): client_timeout=int(arg)
	    if opt in ("-s", "--sort-type"): sort_type=str(arg)
	    if opt in ("-P", "--pem-file"): pemfile=str(arg)

	try:
		# Verify that we have a pem file
		try:
			temp = os.stat(pemfile)
		except OSError:
			print 'No pem file given. Use -P'
			exit(-1)

		if nmap_commands_file != '':
			if verbose_level > 0:
				version()


			# Set up logger
			# Set up a specific logger with our desired output level
			logger_name = 'MyLogger'
			mlog = logging.getLogger(logger_name)

			# Set up the log level
			numeric_level = getattr(logging, log_level.upper(), None)
			if not isinstance(numeric_level, int):
				raise ValueError('Invalid log level: %s' % loglevel)
			mlog.setLevel(numeric_level)

			# Add the log message handler to the logger
			handler = logging.handlers.RotatingFileHandler(log_file, backupCount=5)

			formater = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
			handler.setFormatter(formater)
			mlog.addHandler(handler)

			# End logger


			# First fill the variable from the file
			read_file_and_fill_nmap_variable()

			# Start processing clients
			process_nmap_commands(logger_name)
			print "we have that many commands to complete"
			print len(nmap_command)



		else:
			usage()


	except KeyboardInterrupt:
		# CTRL-C pretty handling.
		print "Keyboard Interruption!. Exiting."
		sys.exit(1)


if __name__ == '__main__':
	# print len(nmap_command)
	# if len(nmap_command) != 0:
	# 	print "len of nmap command is not 0"
		main()
	# else:
	# 	print "len of nmap command is  0"
	# 	quit()

    # main()
