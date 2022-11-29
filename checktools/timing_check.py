#!/usr/bin/env python2

"""
COSMO TECHNICAL TESTSUITE

This script checks whether two runs are bit-identical by comparing the
YUPRTEST files.
"""

# built-in modules
import os, sys, re, json
import argparse

# private modules
sys.path.append(os.path.join(os.path.dirname(__file__), "tools"))
from ts_utilities import read_environ, dir_path
from ts_fortran_nl import get_param
from parseyu import COSMO_Run_yu
import comp_yuprtest

# some global definitions
yufile = 'YUPRTEST'     # name of special testsuite output
yuswitch = 'ltestsuite' # namelist switch controlling YUPRDBG output
nlfile1 = 'INPUT_DIA'    # namelist file containing yuswitch
nlfile2 = 'INPUT_ORG'    # namelist file containing dt


def dir_path(path):
    """decorate a path with a trailing slash if not present"""
    pattern='^(.*)[/]$'
    matchobj=re.match(pattern,path)
    if matchobj:
        return path
    else:
        return path+'/'


def parse():
    env = read_environ()
    rundir = env['RUNDIR']
    yutimings = "YUTIMING"
    cosmolog = env['LOGFILE']
    slurmlog = env['LOGFILE_SLURM']
    name = "Cosmo run in "+rundir
    return COSMO_Run_yu(folder=rundir, name=name, yutimings=yutimings, cosmolog=cosmolog, slurmlog=slurmlog)


def get_reference_timings():
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    env = read_environ()
    rundir = env['RUNDIR']
    timings_file = env['TIMINGS']
    file_path = dir_path(rundir)+timings_file
    config.read(file_path)
    threshold = float(config.get('timings', 'threshold'))
    timings = {}
    for name, value in config.items("timings"):
        if name == "threshold":
            continue
        timings[name] = float(value)
    return (timings, threshold)


def check_value(reference, value, threshold=0):
    if value < (reference*(1.0+threshold/100.0)):
        return True
    return False


def check(data):
    timings, threshold = get_reference_timings()
    status = 0
    for name, timing_ref in timings.iteritems():
        data_timing = data[name]
        if data_timing is None:
            print("Fail: No timing data available for "+name)
        if not check_value(timing_ref, data_timing, threshold=threshold):
            print("Fail: Could not validate "+name+": timing "+str(data_timing)+" (reference timing: "+str(timing_ref)+" with "+str(threshold)+"% threshold)")
            status = 20
        else:
            print(name+": "+str(data_timing)+"s below reference: "+str(timing_ref)+"s with "+str(threshold)+"% threshold")
    return status

def checkjson(data):

    timings, threshold = get_reference_timings()
    status = 0
    dict_data = {}
    for data_point in data:
        dict_data.update({data_point['stencil']: data_point['measurements'][0]})
    for name, timing_ref in timings.iteritems():
        data_timing = dict_data[name]
        if data is None:
            print("Fail: No timing data available for "+name)
        if not check_value(timing_ref, data_timing, threshold=threshold):
            print("Fail: Could not validate "+name+": timing "+str(data_timing)+" (reference timing: "+str(timing_ref)+" with "+str(threshold)+"% threshold)")
            status = 20
        else:
            print(name+": "+str(data_timing)+"s below reference: "+str(timing_ref)+"s with "+str(threshold)+"% threshold")
    return status


def parse_and_write(filename="None"):
    # Parse the logfile and the YUTIMINGS file to get all the relevant data
    data = parse()

    # Convert the format into what we need for the perf-benchmarks
    run2 = {'config': {}, 'runtime': {}, 'times': [], 'metadata': {}}
    for k, v in data.timings:
        run2['times'].append({"measurements": [v], "stencil": k})

    # Convert between cosmo keys and perftool keys
    runtime_info = run2['runtime']
    runtime_info.update({'datetime': data.metadata['Current start time']})
    runtime_info.update({'name': data.metadata['Binary name']})
    runtime_info.update({'version': data.metadata['Tag name']})

    # Addition of all the extra information int metadata
    def without_keys(d, keys):
        return {k: v for k, v in d.items() if k not in keys}
    used_keys = {'Current start time', 'Binary name', 'Tag name'}
    for k, v in without_keys(data.metadata, used_keys).iteritems():
        run2['metadata'][k] = v
    # Write the json-file
    if filename == "None":
        from datetime import datetime
        date = datetime.strptime(data.metadata['Current start time'], '%Y-%m-%d %H:%M')
        filename = str(date.year) + "-" + str(date.month) + "-" + str(date.day) + "-" + str(date.hour) + "-" + \
                   str(date.minute) + "-" + str(date.second) + ".json"

    with open(filename, 'w') as outfile:
        json.dump(run2, outfile, indent=2, sort_keys=True)


def check_tolerance(filename="None"):
    if filename == "unknown":
        print "None"
        return 20
    else:
        with open(filename) as f:
            data = json.load(f)
        timing = data['times']
        return checkjson(timing)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', '-f', type=str,
                                     help='filename of the output json file', dest='filename')
    args = parser.parse_args()
    print(args.filename)
    #parse the inputfile and write to the passed arugment
    parse_and_write(args.filename)
    # parse_and_write()

    # check timings form the tolerance file and abort if it does not pass
    status = check_tolerance(args.filename)
    if status == 20:
        sys.exit(status)




