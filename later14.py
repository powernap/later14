#!/usr/bin/env python3
#
#Copyright (c) 2018, Nick Principe
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:
#
#* Redistributions of source code must retain the above copyright notice, this
#  list of conditions and the following disclaimer.
#
#* Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#------------------------------------------------------------------------------ 
# USAGE:
# later14.py - aggregate per-iteration, per-client, per-op latency data from a
#            SPEC SFS(tm) 2014 benchmark run
# etc.
#------------------------------------------------------------------------------ 
# Authors:
#    - Nick Principe <nick@princi.pe; nap@ixsystems.com>
#------------------------------------------------------------------------------ 
# Version History:
# ----------------
# 0.1 - First somewhat usable incarnation
#------------------------------------------------------------------------------ 
# TODO
#    - Collect/aggregate latency histogram data from sfsc files
#    - Fix obvious and easy PEP8 violations (sorry)
#    - Add a report type to look for outliers - especially in stddev data
#      per-client per-iteration to see if one client was being unreliable

import argparse
import re
import os
import sys
import statistics
import csv

output_file = None
hosts = {}
sfsc_files = []

class SFSThread:
    """An SFS 2014 proc for which we have latency data for a single SFS 2014 run"""
    thread_id = None
    ops_data = None
    lat_data = None
    VALID_OPS = ['write', 'write_file', 'mmap_write', 'mmap_read', 'read', 
            'read_file', 'mkdir', 'rmdir', 'unlink', 'unlink2', 'create',
            'stat', 'append', 'lock', 'access', 'chmod', 'readdir', 
            'random_write', 'random_read', 'read_modify_write', 'open file',
            'close file', 'copyfile', 'rename', 'statfs', 'pathconf', 
            'custom1', 'custom2']

    #TODO: lat bands

    def __init__(self, thread_id, detailstxt):
        """Load in the thread run data from the Details block in an sfsc log file"""
        self.thread_id = thread_id
        self.ops_data = {}
        self.lat_data = {}
        matches = re.findall("\s+(\w+(?: file)?)\s+ops =\s+(\d+)\s+Avg Latency:\s+((?:\d+.\d+)|Not collected)", detailstxt, re.IGNORECASE)
        for match in matches:
            if match[0].lower() in SFSThread.VALID_OPS:
                try:
                    self.ops_data[match[0].lower()] = int(match[1])
                except ValueError:
                    print("Invalid op count {} for op {}. Setting to zero.".format(
                        match[1],match[0].lower()), file=sys.stderr)
                    self.ops_data[match[0].lower()] = 0
                try:
                    self.lat_data[match[0].lower()] = float(match[2]) * 1000 # convert to ms
                except ValueError:
                    self.lat_data[match[0].lower()] = 0.0
            else:
                print("Invalid op \"{}\" encountered. Ignoring.".format(match[1]), file=sys.stderr)

class SFSHost:
    """A host for which we have latency data for a number of SFS2014 runs"""
    hostname = None
    iters = None
    iterdata = None

    def __init__(self, hostname):
        """Create a host that participated in an SFS2014 run"""
        self.hostname = hostname
        self.iters = []
        self.iterdata = {}

    def addLatencyData(self, iteration, thread, details):
        if iteration in self.iters:
            pass
        else:
            self.iters.append(iteration)
            assert(iteration not in self.iterdata)
            self.iterdata[iteration] = {}
        assert thread not in self.iterdata[iteration]
        self.iterdata[iteration][thread] = SFSThread(thread,details)

    def getRunLatStats(self, iteration):
        latstats = {}
        if iteration in self.iters:
            for op in SFSThread.VALID_OPS:
                lats = []
                for t_id,thread in self.iterdata[iteration].items():
                    if thread.ops_data[op] > 0:
                        lats.append(thread.lat_data[op])
                if len(lats) > 0:
                    latstats[op] = {}
                    latstats[op]['min'] = min(lats)
                    latstats[op]['avg'] = statistics.mean(lats)
                    latstats[op]['med'] = statistics.median(lats)
                    latstats[op]['max'] = max(lats)
                    latstats[op]['pstdev'] = statistics.pstdev(lats)
                    latstats[op]['stdev'] = statistics.stdev(lats)
        return latstats

    def getAllRunLatStats(self):
        latstats = {}
        for iteration in self.iters:
            latstats[iteration] = self.getRunLatStats(iteration)
        return latstats

def get_run_data(filename, hosts):
    mf = open(filename,mode='r')

    run_num = None
    run_data = []

    for line in mf:
        Mrun = re.search("Run (\d+) of (\d+)",line,re.IGNORECASE)
        if Mrun:
            if None != run_num:
                parse_run_data(run_num, run_data, hosts)
                run_data = []
            run_num = int(Mrun.group(1))
        else:
            if None != run_num:
                run_data.append(line)
            else:
                continue
    mf.close()

def parse_run_data(run_num, run_data, hosts):
    client = None
    cl_id = None
    cl_data = ""
    for line in run_data:
        Mclid = re.search("Client\s+(\S+)\s+ID:\s+(\d+)\s+",line,re.IGNORECASE)
        if Mclid:
            if None != client:
                if client in hosts:
                    pass
                else:
                    hosts[client] = SFSHost(client)
                hosts[client].addLatencyData(run_num, cl_id, cl_data)
                cl_data = ""
            client = Mclid.group(1)
            cl_id = Mclid.group(2)
        else:
            if None != client:
                cl_data += line
            else:
                continue
    hosts[client].addLatencyData(run_num, cl_id, cl_data)
    cl_data = ""

def print_all_lat_data(hosts):
    file_out = sys.stdout
    wr = None
    if output_file is not None:
        file_out = open(output_file, mode='w')
    wr = csv.writer(file_out, dialect='excel')
    wr.writerow(['Client','Iteration','Operation','min(Latency)',
            'avg(Latency)','median(Latency)','max(latency)',
            'pstdev(Latency)','stdev(Latency)'])
    for hostname,client in hosts.items():
        clrunlat = client.getAllRunLatStats()
        for runnum,rundat in clrunlat.items():
            for op,opdat in rundat.items():
                wr.writerow([hostname, runnum, op, opdat['min'],
                        opdat['avg'], opdat['med'], opdat['max'],
                        opdat['pstdev'], opdat['stdev']])

parser = argparse.ArgumentParser(
        description='Aggregate per-iteration, per-client, per-op latency data from a SPEC SFS(tm) 2014 benchmark run'
        )
parser.add_argument('-i', action='append', nargs='+', help='sfsc file(s)', 
                    required=True, metavar='sfsc_file',
                    )
parser.add_argument('-o', action='store', metavar='output_csv',
                    help='output file, omit for STDOUT',
                    )

args = parser.parse_args()

# Flatten the input file arrays to a single list of files
for sub_list in args.i:
    for item in sub_list:
        sfsc_files.append(item)
# Set the output file appropriately, leave it None for STDOUT
if args.o is not None:
    if (os.path.exists(args.o)):
        print('The specified output file "{}" already exists'.format(args.o))
        sys.exit(2)
    elif (os.path.isdir(os.path.dirname(args.o))):
        print('The specified output directory "{}" does not exist'.format(
            os.path.dirname(args.o)))
        sys.exit(2)
    else:
        output_file = args.o


for mfile in sfsc_files:
    get_run_data(mfile, hosts)

print_all_lat_data(hosts)
