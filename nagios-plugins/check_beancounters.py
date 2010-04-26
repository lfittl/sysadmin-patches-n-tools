#!/usr/bin/python

import re, pickle, os, optparse, sys

cmd_parser = optparse.OptionParser(description="A Nagios plugin that tracks OpenVZ values and alerts if failcnt increases",
                                                                        prog="check_beancounters",
                                                                        version="0.1")

cmd_parser.add_option('-w', action='store', dest='warning_range', type='int', nargs=1, default=1, help="Set increment for warning response, default=1")
cmd_parser.add_option('-c', action='store', dest='critical_range', type='int', nargs=1, default=10, help="Set increment for critical response, default=10")
cmd_parser.add_option('-f', action='store', dest='check_file', nargs=1, default='/tmp/nagios_check_beancounters', 
                                                help="This script uses a text file to store information, you can specify the file here")

options, arguments = cmd_parser.parse_args()

# Globals
allvz = {}
countfile = open('/proc/user_beancounters', 'r').readlines()
check_file= options.check_file
errors = []
exit_status_msg = [ 0 ]

# The bean counters (/proc/user_beancounters) parser, puts the data in the allvz object
# allvz's data structure is nested, a list within a dictionary with a dictionary:
# { VZID:{ VPS_RESOURCE:[ held, maxheld, barrier, limit,    c ] } }
counter = 0
vzmatch = re.compile(r'(?P<vzid>\d+):')
for line in countfile:
        if vzmatch.search(line):
                vzid = vzmatch.search(line).group(1)
                counter = 1
                line_without_vzid = vzmatch.split(line)[2].split()
                allvz[vzid] = { line_without_vzid[0] : line_without_vzid[1:] }
        elif counter:
                allvz[vzid][line.split()[0]] = line.split()[1:]

# If file does not exsist create the allvz pickle file
if not os.path.exists(check_file):
        previous_check_file = open(check_file, 'w')
        pickle.dump(allvz, previous_check_file)
        previous_check_file.close()

# Open the last check
previous_check_file = open(check_file, 'r')
previous_check = pickle.load(previous_check_file)
previous_check_file.close()

# Check fail count
for vz in allvz.keys():
        for item in allvz[vz].keys():
                current_failcnt = int(allvz[vz][item][4])
                # This try statement is so the script does not fail if a new vz has been created
                try:
                        previous_failcnt = int(previous_check[vz][item][4])
                except KeyError:
                        previous_failcnt = 0
                if current_failcnt > previous_failcnt:
                        errors.append(['The failcnt for the ' + item + ' parameter on vz ' + vz + ', has increased from ' + str(previous_failcnt) + ' to ' + str(current_failcnt), current_failcnt - previous_failcnt]) 

# Save when done with the check
previous_check_file = open(check_file, 'w')
pickle.dump(allvz, previous_check_file)
previous_check_file.close()

# The alerting
if errors:
        for itteration, error in enumerate(errors):
                if error[1] >= options.warning_range and error[1] < options.critical_range:
                        exit_status_msg[0] = 1
                        exit_status_msg.append(error[0])
                        del errors[itteration]
        for itteration, error in enumerate(errors):
                if error[1] >= options.critical_range:
                        exit_status_msg[0] = 2
                        exit_status_msg.append(error[0])
                        del errors[itteration]
else:
        exit_status_msg[0] = 0

if exit_status_msg:
        print ' '.join(exit_status_msg[1:]).replace('\n', '')

sys.exit(exit_status_msg[0])
