#!/usr/bin/env python2

"""
COSMO TECHNICAL TESTSUITE

This script checks whether two runs are bit-identical by comparing the
YUPRTEST files.
"""

# built-in modules
import os, sys

# private modules
sys.path.append('./tools/') 
sys.path.append('../checktools/tools') 
sys.path.append('../perf-benchmarks/checktools/tools')
from ts_utilities import read_environ, dir_path
from ts_fortran_nl import get_param
import comp_yuprtest

# some global definitions
yufile = 'YUPRTEST'     # name of special testsuite output
yuswitch = 'ltestsuite' # namelist switch controlling YUPRDBG output
nlfile1 = 'INPUT_DIA'    # namelist file containing yuswitch
nlfile2 = 'INPUT_ORG'    # namelist file containing dt

def check():

    # get name of myself
    myname = os.path.basename(__file__)
    header = myname+': '

    # get environment variables
    env = read_environ()
    verbose = int(env['VERBOSE'])
    rundir = dir_path(env['RUNDIR'])
    refoutdir = dir_path(env['REFOUTDIR'])
    namelistdir = dir_path(env['NAMELISTDIR'])
    tolerance = env['TOLERANCE']
    forcematch = int(env['FORCEMATCH'])
   
    # defines the 2 file that belongs logically to the checker
    yufile1 = rundir + yufile
    yufile2 = refoutdir + yufile

    # extract timestep
    try:
        dt = float(get_param(rundir+nlfile2, 'dt'))
    except:
        if verbose:
            print header+'failed to extract dt from '+rundir+nlfile2
        return 20 # FAIL

    # check if special testsuite output was activated
    if get_param(rundir+nlfile1, yuswitch) in ['.FALSE.', '.false.']:
        if verbose:
            print yuswitch+' is set to .false. in '+rundir+nlfile1+' for this simulation'
        return 20 # FAIL

    #check if tolerance file exists in namelistdir or type dir
    tolerance_path_1=namelistdir + tolerance
    tolerance_path_2=namelistdir + '../'+ tolerance
    if os.path.exists(tolerance_path_1):
        tolerance_file=tolerance_path_1   #in namelist dir
        ltol_file=True
    elif  os.path.exists(tolerance_path_2):
        tolerance_file=tolerance_path_2   #in type dir
        ltol_file=True
    else:
        tolerance_file=''
        ltol_file=False      


    # define tolerances for comparing YUPRTEST files
    # Use tolerance file if exists
    if ltol_file:
        if verbose > 1:
            print header + 'Using tolerance values from file '+tolerance_file
        

        try:       
            tol_times  = get_param(tolerance_file,'tol_times')
            tol_times  = [float(x) for x in tol_times.split(',')]
            tol_temp = get_param(tolerance_file,'tol_temp')
            tol_temp = [float(x) for x in tol_temp.split(',')]
            tol_all  = get_param(tolerance_file,'tol_all')
            tol_all  = [float(x) for x in tol_all.split(',')]
            minval = float(get_param(tolerance_file,'minval'))
        except:
            if verbose:
                print header+'Error while reading '+tolerance_file
                print header+'Cannot read one of the follwoing parameter: tol_times,tol_temp,tol_all,minval'
            return 20 # FAIL 
    else:
        if verbose > 1:
            print header + 'Using default tolerance values'

        tol_times = [1200,2400,3600]  # time limit for tolerance setting in seconds
        tol_temp = [1.0e-9,1.0e-5,1.0e-3] # tolerance threshold for temperature field for 
                                      # tol_times[i] < t <= tol_times[i+1]
        tol_all  = [1.0e-7,1.0e-4,1.0e-0] # tolerance threshold for all other prognostic fields  
                                      # for tol_times[i] < t <= tol_times[i+1]
                
        minval    = 1.0e-9    # values below min val are not considered

    # set tolerance time step index
    nts  = [int(x/dt) for x in tol_times]

    # override in case FORCEMATCH is set
    if forcematch == 1:
        print('NOTE: setting thresholds to enforce bit-reproducibility')
        minval = -1
        nts = [10000]
        tol_temp = [0.0]
        tol_all = [0.0]

    try:
        # check for bit identical results
        if verbose > 1:
            print header + 'Checking first if results are bit identical'
        if verbose > 2:
            print header + 'comp_yuprtest()'
            print header + '  file1 = '+yufile1
            print header + '  file2 = '+yufile2
            print header + '  minval = '+str(-1)
            print header + '  nts = [%s]' % ','.join(map(str, [10000]))
            print header + '  tol_temp = [%s]' % ','.join(map(str, [0.0]))
            print header + '  tol_all = [%s]' % ','.join(map(str, [0.0]))
        err_count_identical = comp_yuprtest.cmp_(yufile1, yufile2, -1, -1, [10000], [0.0], [0.0])
        if verbose > 1:
            if err_count_identical == 0:
                print header + 'Results are bit identical'
            else:
                print header + 'Results are not bit identical'
        # check if results are within tolerance values
        if verbose > 1:
            print header + 'Checking if results are within tolerance'
            print header + '  minimal value : %s' %(minval)
            print header + '  tolerance time : %s' % ','.join(map(str, tol_times))
            print header + '  corresponding time step : %s' % ','.join(map(str, nts))
            print header + '  thresholds for temperature field: %s' % ','.join(map(str, tol_temp))
            print header + '  thresholds for all prognostic fields: %s' % ','.join(map(str, tol_all))
        if verbose > 2:
            print header + 'comp_yuprtest()'
            print header + '  file1 = '+yufile1
            print header + '  file2 = '+yufile2
            print header + '  minval = '+str(minval)
            print header + '  nts = [%s]' % ','.join(map(str, nts))
            print header + '  tol_temp = [%s]' % ','.join(map(str, tol_temp))
            print header + '  tol_all = [%s]' % ','.join(map(str, tol_all))    
        error_count = comp_yuprtest.cmp_(yufile1, yufile2, 0, minval, nts, tol_temp, tol_all)
        if verbose > 1:
            if error_count == 0:
                print header + 'Results are within thresholds'
            else:
                print header + 'Results are not within thresholds'

    except Exception as e:
        if verbose:
            print e
        return 20 # FAIL

    if err_count_identical == 0:
        return 0 # MATCH
    elif error_count == 0:
        return 10 # OK
    else:
        return 20 # FAIL


if __name__ == "__main__":
    sys.exit(check())


