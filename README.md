# later14
A tool to aggregate per-iteration, per-client, per-op latency data from a SPEC SFS(tm) 2014 benchmark run

usage: later14.py [-h] -i sfsc_file [sfsc_file ...] [-o output_csv]

Aggregate per-iteration, per-client, per-op latency data from a SPEC SFS(tm)
2014 benchmark run

optional arguments:
  -h, --help            show this help message and exit
  -i sfsc_file [sfsc_file ...]
                        sfsc file(s)
  -o output_csv         output file, omit for STDOUT

This is intended to assist in performance analysis of a completed SPEC SFS(tm) 2014 benchmark run:
   - Assess variation in response time for procs intra-client
   - .... inter-client
   - Aggregate per-op latency statistics to determine bottlenecks/issues of solution under test

This script outputs a CSV with the following columns:
   - Client (hostname or IP of the load generator)
   - Iteration (run # of SFS 2014 run)
   - Operation (which netmist operation was tested)
   - min(Latency) (the minimum latency for that load generator for that iteration)
   - avg(Latency) (the average latency for that load generator for that iteration)
   - median(Latency) (the median latency for that load generator for that iteration)
   - max(Latency) (the maximum latency for that load generator for that iteration)
   - pstdev(Latency) (the pstdev of latency for that load generator for that iteration)
   - stdev(Latency) (the stdev of latency for that load generator for that iteration)

Operation types for which there was no data collected are not included in the output.

This tool accounts for the fact that load may be distributed unevenly across load generators for a SPEC SFS(tm) 2014 benchmark run, so multiple load generators may exist in a single sfsc* log file. As long as all sfsc log files are passed to the script (via wildcard or multiple -i arguments) all accounting will be done correctly.

This tool is not useful without SPEC SFS(tm) 2014, which is available from SPEC at http://spec.org/sfs2014

Version History:
0.1 - First somewhat usable incarnation

TODO:
   - Collect/aggregate latency histogram data from sfsc files
   - Fix obvious and easy PEP8 violations (sorry)
   - Add a report type to look for outliers - especially in stddev data
     per-client per-iteration to see if one client was being unreliable

Authors:
   - Nick Principe <nick@princi.pe; nap@ixsystems.com>

Thanks to:
   - iXsystems
   - SPEC Storage subcommittee

Apologies to:
   - SPEC, by whom this tool is not authorized or endorsed, and with whom this tool is not affiliated
