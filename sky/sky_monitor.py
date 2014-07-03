#!/usr/bin/env python

import datetime
import os
import sqlite3
import sys

DATABASE = '/usr/local/bin/SKY_Monitor/mon_sky.db'

def query_cache():
    try:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute('SELECT * FROM transfers ORDER BY remote_start_time DESC')
        cached_jobs = cur.fetchall()
    except Exception, e:
        print "Error %s:" % e.args[0]
        sys.exit(1)
    finally:
        if conn:
            conn.close()
    return cached_jobs

if __name__ == '__main__':
    
    # NRPE Exit codes
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3

    if not os.path.isfile(DATABASE):                                                                                                                      
        print 'CRITICAL - Cannot find Signiant cache!'
        sys.exit(CRITICAL)

    now = datetime.datetime.utcnow()
    # [0] First index from list of jobs, [3] is the time entry, divided by 1000000 because time microseconds
    last = datetime.datetime.fromtimestamp(query_cache()[0][3] / 1000000)

    delta = (now - last).seconds

    if delta > 21600:
        print 'CRITICAL - No file has been sent in %0.2f hours.' % (delta / 60.0 / 60.0)
        sys.exit(CRITICAL)
    else:
        print 'OK - The most recent job started %0.2f hours ago.' % (delta / 60.0 / 60.0)
        sys.exit(OK)

