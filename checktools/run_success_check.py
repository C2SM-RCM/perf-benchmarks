#!/usr/bin/env python2

"""
COSMO TECHNICAL TESTSUITE

This script checks whether the standard output of the COSMO simulation
contains the words "CLEAN UP" which is indicative of a fully successful
simulation
"""

# built-in modules
import os, re, sys

# private modules
sys.path.append(os.path.join(os.path.dirname(__file__), "tools"))
from ts_utilities import read_environ, dir_path

# information
__author__     = "Nicolo Lardelli, Oliver Fuhrer"
__copyright__  = "Copyright 2012, COSMO Consortium"
__license__    = "GPL"
__version__    = "1.0"
__date__       = "Mon Oct  8 15:37:57 CEST 2012"
__email__      = "cosmo-wg6@cosmo.org"
__maintainer__ = "xavier.lapillonne@meteoswiss.ch"


def check():

    # initialize status
    status = 0 # MATCH

    # get name of myself
    myname = os.path.basename(__file__)
    header = myname+': '

    # get environment variables
    env = read_environ()
    verbose = int(env['VERBOSE'])
    rundir = env['RUNDIR']
    logfile = dir_path(rundir) + env['LOGFILE']
   
    if verbose>2:
        print header + 'checking presence of CLEAN UP cleanup line in '+logfile

    try:
        file = open(logfile,'r')
        pattern = '(.*)^(.*)CLEAN(\s)UP(.*)'
        result = 30 # CRASH
        for text in file:
            if re.match(pattern, text):
                result = 0 # MATCH
        file.close()

    except:
        if verbose:
            print header+'failed to open '+logfile
        result = 30 # CRASH

    return result


if __name__ == "__main__":
    sys.exit(check())

