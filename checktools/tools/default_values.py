class DefaultValues:
    """Datacontainer for the default values of the command line options"""
    
    nprocs   = 16
    nprocio  = None
    v_level  = 1
    mpicmd   = "aprun -n"
    exe      = None
    steps    = None
    stdout   = ""
    testlist = "testlist.xml"
    tolerance = "TOLERANCE"
    timeout  = None
    forcematch = 0

