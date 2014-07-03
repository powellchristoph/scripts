#!/usr/bin/env python

import logging
import os
import smtplib
import subprocess
import sys
import time

from datetime import datetime as dt

# Encompass Aspera creds
asp_user = r''               # Aspera username
asp_pass = r''               # Aspera password
asp_server = ''              # Aspera host

# List of people that receive success emails
success_email_to = [ ]
# List of people that receive start emails
start_email_to = success_email_to
# List of people that receive error emails
error_email_to = [ ]

align_dir = ''     # alignlinear home diretcory

log_level = logging.DEBUG
log_file = '/root/bin/align_to_encompass.log'
pid_file = '/var/run/align_to_encompass.pid'
send_list = '/root/bin/align_filelist.txt'


#****************************************************************************************************
# Functions
#****************************************************************************************************
def send_email(filelist, type, error=None):

    servername = ''
    from_address = ''

    to = []
    subject = 'Align Linear Notification - '
    if type == 'start':
        subject += 'Start'
        msg = "Found the following files, starting transfer to Encompass...\n\n%s" % '\n'.join(filelist)
        to.extend(start_email_to)
    elif type == 'success':
        subject += 'Success'
        msg = "The following files were successfully delivered to Encompass...\n\n%s" % '\n'.join(filelist)
        to.extend(success_email_to)
    elif type == 'error':
        subject += 'Failure'
        msg = "There was an error transferring the following files...\n\n%s\n%s" % (error, '\n'.join(filelist))
        to.extend(error_email_to)

    message = """\
From: %s
To: %s
Subject: %s

%s
""" % (from_address, ', '.join(to), subject, msg)

    server = smtplib.SMTP(servername)
    server.sendmail(from_address, to, message)
    server.quit()

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

    debug('Searching for files...')
    filelist = [os.path.join(align_dir, f) for f in os.listdir(align_dir) if not f.startswith('.') or os.path.isfile(f)] 

    if filelist:
        debug('Found files...%s' % filelist)
        # Write out filelist
        fl = open(send_list, 'w')
        fl.write('\n'.join(filelist) + '\n')
        fl.close()
    
        # Send email with filelist
        debug('Sending start email.')
        send_email(filelist, 'start')
    
        # Transfer the files
        aspera_cmd = 'ASPERA_SCP_PASS="%s" ' % asp_pass
        aspera_cmd += '/usr/bin/ascp --ignore-host-key --mode=send --file-list=%s --host=%s --user=%s --remove-after-transfer -k2 -d -l 75M -m 10K -TQ /' % (send_list, asp_server, asp_user)

        debug(aspera_cmd)

        info('Transfering %s' % filelist)
        proc = subprocess.Popen(aspera_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = proc.communicate()

        # Email success/failure
        if proc.returncode == 0:
            debug('Sending success email')
            send_email(filelist, 'success')
        else:
            error('Transferred failed!! %s' % stderr)
            debug('Sending failure email')
            send_email(filelist, 'error', stderr)

        os.remove(send_list)
    else:
        debug('No files found.')

    os.remove(pid_file)
