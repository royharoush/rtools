#!/usr/bin/python

import json
import sys

try:
	filename = sys.argv[1]
except:
	print "Usage: " + sys.argv[0] + " [JSON_file_name]"
	sys.exit(1)
try:
	f = open(filename, "r")
except:
	print "Unknown file " + filename
	sys.exit(1)
try:
	obj = json.loads(f.read())
except:
	print "Bad JSON found at " + filename
	sys.exit(1)

#Get all possible keys
all_keys = []
for server in obj.keys():
	server_id = server
	for key in obj[server].keys():
		if key not in all_keys:
			all_keys.append(key)

#Print all keys as headers for CSV
output = "server id,"
for key in all_keys:
	output += key + ","

print output[:-1]

#Print CSV lines
for server in obj.keys():
	server_id = server
	output = server + ","
	for key in all_keys:
		if key in obj[server].keys():
			output += str(obj[server][key])
		output +=","
	print output[:-1]