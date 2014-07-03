#!/usr/bin/env python

import datetime
import os
import sqlite3
import sys
from suds.client import Client

## Signiant vars
SIGSERV = ''
SIGUSER = ''
SIGPASS = ''
SKY_JOB_GROUP = 'vub_outgest_external'
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

def query_signiant(name):
    stats = client.service.getStats(
            SIGUSER,
            SIGPASS,
            name,
            SKY_JOB_GROUP,
            0,
            'remote_start_time, remote_end_time',
            ",",
            ";")
    if stats:
        r = stats.split(',')
        src_agent = r[2]
        dest_agent = r[3]
        remote_start_time = r[4]
        remote_end_time = r[5].split(';')[0]
        return (src_agent, dest_agent, remote_start_time, remote_end_time)
    else:
        raise Exception('Stats not returned for job: %s' % name)

if __name__ == '__main__':

    if not os.path.isfile(DATABASE):                                                                                                                      
        print 'Cannot find Signiant cache, please create the db...'
        sys.exit(1)

    # Query all cached jobs in the db
    cached_job_names = [row[0] for row in query_cache()]

    # Query all jobs from Signiant
    # Create SOAP client and connect to Signiant
    url='https://' + SIGSERV + '/signiant/services/SchedulerService?wsdl'
    client = Client(url)
    sig_jobs = client.service.listJobs(SIGUSER, SIGPASS, SKY_JOB_GROUP).split(', ')

    # Compare and get new jobs
    new_jobs = set(sig_jobs).difference(set(cached_job_names))

    # Query new jobs and add them to cache
    if new_jobs:
        print 'Found %d new jobs' % len(new_jobs)
        try:
            conn = sqlite3.connect(DATABASE)
            cur = conn.cursor()
            for job in new_jobs:
                try:
                    src, dest, start_time, end_time = query_signiant(job)
                    print 'Adding %s to cache...' % job
                except Exception, e:
                    print str(e)
                    continue
                statement = 'INSERT INTO transfers (name, src_agent, dest_agent, remote_start_time, remote_end_time) VALUES ("%s", "%s", "%s", %s, %s)' % (job, src, dest, start_time, end_time)
                cur.execute(statement)
                conn.commit()
        except sqlite3.Error, e:
            print "Error %s:" % str(e)
            sys.exit(1)
        finally:
            if conn:
                conn.close()
    else:
        print "No new jobs found."
