#!/usr/bin/env python
 
"""
Description: A basic wrapper script around the mysqlbackup utility. 
  This will execute a compressed backup and the sync the logs. The
  resulting back up is a full backup that you can restore from. It
  will also rotate the existing backups.

Author: Chris Powell
Date: 8/14/2013
Version: 0.1
"""

#-----------Variables -------------------------------------
DATA_DIR        = '/var/lib/mysql_drbd'
DEFAULTS_FILE   = '/var/lib/mysql_drbd/my.cnf'
PORT            = '3306'
SOCKET          = '/var/lib/mysql/mysql.sock'
BACKUP_DIR      = "/var/lib/mysql_drbd/backups"
BACKUP_CMD      = '/opt/mysql/meb-3.8/bin/mysqlbackup'
BACKUP_USER     = 'dba'
BACKUP_PASS     = 'LFwrXDen'
READ_THREADS    = '1'
PROCESS_THREADS = '6'
WRITE_THREADS   = '1'
LIMIT_MEMORY    = '300'
RETENTION_TIME  = 30 # Time in number of days
NAGIOS_ALERT    = '/etc/nagios/mysql_backup_alert.txt'

import datetime as dt
import getopt
import os
import shutil
import subprocess
import sys
import time

def usage():                                                                                                            
    print "Usage:"
    print "%s [ -f --full | -i --incremental ] --nagios " % sys.argv[0]
    print
    print
    print " --full:             Execute a full backup."
    print " --incremental:      Execute an increamental backup."
    print " --nagios:           Will create the nagios alert file."
    print " --help:             Show this message."

def die(msg, err=None, alert_nagios=False):
    print msg

    if err:
        print str(err)

    if alert_nagios:
        with open(NAGIOS_ALERT, 'w') as f:
            f.write(msg + '\n')
    exit(1)

def check_sanity(nagios=False):
    if not os.path.ismount(DATA_DIR):
        die('%s is not mounted...' % DATA_DIR, alert_nagios=nagios)

    if not os.path.isdir(BACKUP_DIR):
        die('%s does not exist' % BACKUP_DIR, alert_nagios=nagios)

    if not os.path.isfile(DEFAULTS_FILE):
        die('%s does not exist' % DEFAULTS_FILE, alert_nagios=nagios)

    if not os.path.exists(BACKUP_CMD):
        die('%s does not exist' % BACKUP_CMD, alert_nagios=nagios)

    if not os.path.exists(SOCKET):
        die('The MySQL service does not appear to be running.', alert_nagios=nagios)

def execute(cmd, name, nagios=False):
    tic = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    stdout, stderr = proc.communicate()
    toc = time.time()
    if proc.returncode != 0:
        die('The %s process failed!: %s' % (name, cmd), stdout, alert_nagios=nagios)

    return (stdout, toc - tic)

# Main ###################################################################################
if __name__ == '__main__':

    do_full = False
    do_incremental = False
    do_nagios = False

    args = sys.argv[1:]                                                                                                 
    try:
        (opts, getopts) = getopt.getopt(args, 'fih?',
                ['full', 'incremental', 'nagios', 'help'])

    except:
        usage()
        die('\nInvalid command line option detected.')

    for opt, arg in opts:
        if opt in ('-h', '-?', '--help'):
            usage()
            sys.exit(0)
        if opt in ('-f', '--full'):
            do_full = True
        if opt in ('-i', '--incremental'):
            die('This option has not been implemented yet.')
            do_incremental = True
        if opt == '--nagios':
            do_nagios = True

    if do_full and do_incremental:
        die('You cannot execute a full and incremental at the same time.')
    elif not do_full and not do_incremental:
        die('You must specify either full or incremental')

    check_sanity(nagios=do_nagios)

    # Create backup 
    print 'Creating backup now...'
    now = dt.datetime.now()
    timestamp = now.strftime('%Y-%m-%d_%H-%M-%S')
    command = '{cmd} --defaults-file={defaults_file} --user={user} --password={password} --port={port} --socket={socket} --backup-dir={dir} --compress --read-threads={read} --process-threads={process} --write-threads={write} --limit-memory={memory}  backup'.format(
               cmd              = BACKUP_CMD,
               defaults_file    = DEFAULTS_FILE,
               user             = BACKUP_USER,
               password         = BACKUP_PASS,
               port             = PORT,
               socket           = SOCKET,
               dir              = os.path.join(BACKUP_DIR, timestamp),
               read             = READ_THREADS,
               write            = WRITE_THREADS,
               process          = PROCESS_THREADS,
               memory           = LIMIT_MEMORY
            )

    output, time_done = execute(command, 'compressed-backup', nagios=do_nagios)
    with open(os.path.join(BACKUP_DIR, timestamp, 'backup.log'), 'a') as f:
        f.write(output)
    if 'mysqlbackup completed OK!' not in output:
        print 'Completed, but something strange happened. Please verify the output at /%s/backup.log (%f sec)' % (BACKUP_DIR, time_done)
    else:
        print 'Completed (%f sec)' % time_done

    # Apply logs
    print 'Applying the log...'
    command = '{cmd} --backup-dir={dir} --uncompress --read-threads={read} --process-threads={process} --write-threads={write} --limit-memory={memory} apply-log'.format(
            cmd     = BACKUP_CMD,
            dir     = os.path.join(BACKUP_DIR, timestamp),
            read             = READ_THREADS,
            write            = WRITE_THREADS,
            process          = PROCESS_THREADS,
            memory           = LIMIT_MEMORY
        )
    output, time_done = execute(command, 'apply-log', nagios=do_nagios)
    with open(os.path.join(BACKUP_DIR, timestamp, 'apply-log.log'), 'a') as f:
        f.write(output)
    if 'mysqlbackup completed OK!' not in output:
        print 'Completed, but something strange happened. Please verify the output at /%s/apply-logs.log (%f sec)' % (BACKUP_DIR, time_done)
    else:
        print 'Completed (%f sec)' % time_done

    print 'Backup written to %s\n' % os.path.join(BACKUP_DIR, timestamp)

    # Rotate backups
    print 'Rotating backups older than %s days...' % RETENTION_TIME
    tic = time.time()
    dirs = [os.path.join(BACKUP_DIR, d) for d in os.listdir(BACKUP_DIR) if os.path.isdir(os.path.join(BACKUP_DIR, d))]
    for d in dirs:
        file_date = dt.datetime.strptime(os.path.basename(d), '%Y-%m-%d_%H-%M-%S')
        if (now - file_date).days > RETENTION_TIME:
            try:
                print 'Removing %s' % d
                shutil.rmtree(d)
            except Exception, e:
                print 'There was an error deleting %s' % d
                print str(e)
    toc = time.time()
    print 'Completed (%f sec)' % (toc - tic)

    if os.path.exists(NAGIOS_ALERT):
        os.remove(NAGIOS_ALERT)
