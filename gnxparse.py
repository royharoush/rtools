#!/usr/bin/env python

# GNXParse - Glens Nmap XML Parser

# Print list of active hosts, ports, or subnets (/24) from nmap xmp results
# Output (nmap) command lines for retesting hosts
#
# Project URL: https://bitbucket.org/memoryresident/gnxtools
# Author URL: https://www.glenscott.net

# todo:
# - Add JSON output support
# - Add in better support for TCP/UDP filtering. At the moment the script just deals with 'open ports' regardless of protocol.

import sys, argparse
try:
    import  xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


def handle_opts(nmap_rescan_cmd):
	parser = argparse.ArgumentParser(
		formatter_class=argparse.RawDescriptionHelpFormatter,
		description='Glens Nmap XML Parser (gnxparse)',
		usage='%(prog)s filename.xml [OPTIONS]',
		epilog="""\
usage examples:
	%(prog)s ./scan.xml -ips 
	%(prog)s ./scan.xml -ports 
	%(prog)s ./scan.xml -subnets 
	%(prog)s ./scan.xml -rescan > ./outputscript.sh
	%(prog)s ./scan.xml -rescan 'nmap -A' > ./outputscript.sh
	%(prog)s ./scan.xml -i -s -r 
	%(prog)s ./scan.xml -i -s -r 'nmap -A' """
	)

	parser.add_argument('file', action='store',
                   help='File containing nmap XML output')
	parser.add_argument('-i', '-ips', action='store_true', dest='ips',
                   help='Output list of active ipv4 addresses')
	parser.add_argument('-p', '-ports', action='store_true', dest='ports',
                   help='Output list of open ports')
	parser.add_argument('-s', '-subnets', action='store_true', dest='subnets',
                   help='Output list of /24 subnets containing live hosts')
	parser.add_argument('-r', '-rescan', action='store', dest='rescan', nargs='?', default='not_set',
                   help='Generate nmap-compatible command-line for re-testing hosts. If no nmap command prefix is given, defaults to: ' + nmap_rescan_cmd)
	parser.add_argument('-c', '-csv', action='store', dest='csvout', nargs='?', default='not_set',
                   help='Output simple csv file format (HOSTIP,port1,port2,port3)')	
	parser.add_argument('-q', '-quiet', action='store_true', dest='suppressheaders',
                   help='Suppress header output for ip, port and subnet lists.')					   
	parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0 (http://bitbucket.org/memoryresident/gnxtools )'
	)

	args = parser.parse_args()
	
	return args
	
def parse_ips(nmap_results):
	# Parse the xml for all IPv4 addresses which are good keys for each set of results
	host_ip_list = [];
	
	for host in nmap_results.findall('host'):
		for hostip in host.iterfind('address[@addrtype="ipv4"]'):
			host_ip_list.append(hostip.get('addr'))
	
	return host_ip_list 

	
def parse_ports(nmap_results):
	# Parse the xml for a list of all open ports, deduplicate and return
	
	open_port_list = [];
	deduped_open_port_list = []
	
	# should add in filter for TCP/UDP at some stage.
	for port in nmap_results.iter('port'):
		for portstate in port.iterfind('state[@state="open"]'):
			open_port_list.append(port.get('portid'))
	
	open = set()
	open_add = open.add
	deduped_open_port_list = [ x for x in open_port_list if not (x in open or open_add(x))]
	deduped_open_port_list.sort(key=int)
	
	return deduped_open_port_list

	
def parse_subnets(host_ip_list):
	# Return a simple list of all /24 subnets containing ips
	# For every ip address, put it in format x.x.x.0/24, deduplicate the list and return
	
	subnetlist = [];
	dedupedsubnetlist = []

	for host_line in host_ip_list:
		oct1,oct2,oct3,oct4 = host_line.split('.', 3);
		subnetlist.append(oct1+'.'+oct2+'.'+oct3+'.0/24');
	
	seen = set()
	seen_add = seen.add
	dedupedsubnetlist = [ x for x in subnetlist if not (x in seen or seen_add(x))]		

	return dedupedsubnetlist

def create_rescan_commands(nmap_results, nmap_rescan_cmd):
	# generate a list of single line nmap commands incoporating known open ports for each IP.
	
	port_list = [];
	host_port_command_lines = [];
	
	for host in nmap_results.findall('host'):
		for hostip in host.iterfind('address[@addrtype="ipv4"]'):
			host_ip=hostip.get('addr')
			
		host_port_list = [];

		for port in host.iterfind('./ports/port'):		
			for openport in port.iterfind('state[@state="open"]'):
				host_port_list.append(port.attrib['portid'])
		
		if host_port_list:
			currentcommandline=nmap_rescan_cmd + " " + host_ip + ' -p' + ','.join(map(str,host_port_list)) + ' -oN ./' + host_ip + '.txt' + ' -oX ./' + host_ip + '.xml' 
			host_port_command_lines.append(currentcommandline)
		if not host_port_command_lines:
			host_port_command_lines.append("No open ports in scan results")
			
	return host_port_command_lines

def print_csv_lines(nmap_results):
	# Print ips and ports in simple .csv list
	
	port_list = [];
	csv_lines = [];
	
	for host in nmap_results.findall('host'):
		for hostip in host.iterfind('address[@addrtype="ipv4"]'):
			host_ip=hostip.get('addr')
		host_port_list = [];
		for port in host.iterfind('./ports/port'):		
			for openport in port.iterfind('state[@state="open"]'):
				host_port_list.append(port.attrib['portid'])
		if host_port_list:
			currentcsvline=host_ip +',' + ','.join(map(str,host_port_list)) 
			csv_lines.append(currentcsvline)
		if not csv_lines:
			csv_lines.append("No hosts/open ports in scan results")
	
	return csv_lines

def main ():

	#default nmap command, can be customsed at runtime via -r 'new command'
	#set to default timing no-ping scan with traceroute 
	nmap_rescan_cmd = "nmap -PN --traceroute --open"

	args = handle_opts(nmap_rescan_cmd)

	if args.file == "":
		sys.exit("No Nmap XML file specified. (try --help)")
	else:
		try: 
			nmap_results = ET.ElementTree(file=args.file)
		except:
			sys.exit("Please specify a valid nmap XML file")
		
	# if no options are specified, quit with error
	if not (args.ips or args.subnets or args.ports):
		# args.rescan will only be 'not_set' if it wasn't requested. 
		# -r with no opts will be 'None' and -r with opts will be those opts as a string
		if (args.rescan == "not_set" and args.csvout == "not_set"):
			sys.exit('Require one of -i, -s, -r, -c. (try --help)')
	
	# if rescan requested with args, replace our default nmap command
	if (args.rescan != None and args.rescan != 'not_set'):
		nmap_rescan_cmd = str(args.rescan)
	
	# everything uses the host ip list, so get that first.
	host_ip_list = (parse_ips(nmap_results))
	
	if args.ips == True:
		if not args.suppressheaders == True : 
			print "IPv4 Addresses for live hosts:"
		
		for ip_address in host_ip_list:
			print (ip_address);
	
	if args.ports == True:
		if not args.suppressheaders == True : 
			print "Open Port summary for live hosts:"
		
		open_port_list = parse_ports(nmap_results)
		
		for open_port in open_port_list:
			print (open_port);
	
	if args.subnets == True:
		if not args.suppressheaders == True : 
			print "Subnets containing live hosts:"
		dedupedsubnetlist = (parse_subnets(host_ip_list))
		
		for subnet in dedupedsubnetlist:
			print (subnet);
	
	# Test to see if -r was requested. It will only be 'not set' if it was not requested at all.
	if (args.rescan != 'not_set'):
		print "#!/bin/bash"
		print "#Nmap command lines for retesting hosts:"
		commandlines = create_rescan_commands(nmap_results, nmap_rescan_cmd)
		for line in commandlines:
			print str(line);

	if (args.csvout != 'not_set'):
		csvlines = print_csv_lines(nmap_results)
		for line in csvlines:
			print str(line);
			
if __name__ == "__main__":
   main()
