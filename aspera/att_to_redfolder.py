#!/usr/bin/env python

import logging
import os
import smtplib
import subprocess
import sys
import time
import urllib

from datetime import datetime as dt

#######################################################################
# Defined variables 
#######################################################################
AOD_HOST = ''
AOD_USER = ''
AOD_PASS = ''
 
STORAGE_USER = ''
# Password must be URI encoded including "/"
STORAGE_PASS = urllib.quote('', '')
STORAGE_CONTAINER = 'ingest'
SPEED = 900

source_path = ''
log_level = logging.DEBUG

ASCP = '/usr/bin/ascp'

#######################################################################
# Do not modify below this unless you know what you are doing
#######################################################################

script_name = os.path.basename(__file__)
log_file = '/root/bin/%s.log' % script_name
pid_file = '/var/run/%s.pid' % script_name

# List of people that receive error emails
error_email_to = [ ]

def send_email(filepath, error):

    servername = ''
    from_address = ''

    subject = 'ATT -> Redfolder Delivery Error'
    msg = 'Error Deliverying to Redfolder.\n\nFile: %s\nError: %s' % (filepath, error)
    to = error_email_to
        
    message = """\
From: %s
To: %s
Subject: %s

%s
""" % (from_address, ', '.join(to), subject, msg)

    server = smtplib.SMTP(servername)
    server.sendmail(from_address, to, message)
    server.quit()

def validate(files):
    ''' Checks that the given source is stable and that there is no file system activity. '''

    vfiles = []
    eof = {}

    for filename in files:
        with open(filename, 'rb') as f:
            f.seek(0,2)
            eof[filename] = f.tell()
    
    time.sleep(10)

    for filename in files:
        with open(filename, 'rb') as f:
            f.seek(0,2)
            if f.tell() == eof[filename]:
                vfiles.append(filename)

    return vfiles
        

#****************************************************************************************************
# Main
#****************************************************************************************************
if __name__ == '__main__':

    logging.basicConfig(
            stream=sys.stdout,
#            filename=log_file,
            level=log_level,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%b %d %H:%M:%S')

    debug = logging.debug
    info = logging.info
    warning = logging.warning
    error = logging.error

    # PID file management
    if os.access(pid_file, os.F_OK):
            pd = open(pid_file, 'r')
            old_pd = pd.readline()
            pd.close()
            if os.path.exists("/proc/%s" % old_pd):
                    print "You already have an instance of the program running"
                    print "It is running as process %s" % old_pd
                    sys.exit(1)
            else:
                    print "File is there but the program is not running"
                    print "Removing lock file for the: %s" % old_pd
                    os.remove(pid_file)
    pd = open(pid_file, 'w')
    pd.write("%s" % os.getpid())
    pd.close()

    found_files= []

    debug('Searching for files...')
    dirs = [d for d in os.listdir(source_path) if os.path.isdir(os.path.join(source_path, d))]
    for d in dirs:
        dirpath = os.path.join(source_path, d)
        debug('Checking %s' % dirpath)

        files = [f for f in os.listdir(dirpath) if os.path.isfile(os.path.join(dirpath, f))]
        if files:
            for f in files:
                found_files.append(os.path.join(dirpath, f))
        else:
            debug('No files found at %s...' % d)

    
    debug('Validaing files.')

    for f in validate(found_files):
        # Build the ascp command leave a trailing space or you will break shit
        ascp_cmd = ''
        ascp_cmd += 'ASPERA_DEST_PASS="%s" ' % STORAGE_PASS
        ascp_cmd += 'ASPERA_SCP_PASS="%s" ' % AOD_PASS
        ascp_cmd += '%s -P33001 -O33001 -l %sM -T ' % (ASCP, SPEED)
	ascp_cmd += '-k2 -d --src-base=%s ' % source_path
        ascp_cmd += '--user=%s --host=%s --mode=send %s ' % (AOD_USER, AOD_HOST, f)
        ascp_cmd += 'azu://%s@blob.core.windows.net/%s' % (STORAGE_USER, STORAGE_CONTAINER)
        
        info('Transfering %s' % f)
        #debug(ascp_cmd)

        #ascp_cmd = 'ls /non/existant/path'
        #ascp_cmd = 'sleep 2'
        proc = subprocess.Popen(ascp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = proc.communicate()
        
        # Email success/failure
        if proc.returncode == 0:
            debug('%s was successful.' % f)
            try:
                debug('Removing %s' % f)
                os.remove(f)
            except Exception, err:
                warning('Unable to remove %s: %s' % (f, err))
                send_email(f, err)
        else:
            error('Transferred failed!! %s' % stderr)
            debug('Sending failure email')
            send_email(f, stderr)

    os.remove(pid_file)
