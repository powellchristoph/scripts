#!/usr/bin/env python

from helpers import TransferLog, connect_to_db

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os
import smtplib



if __name__ == "__main__":

    mail_server = ''
    subject = 'Telus Network Report'
    send_to = [ ] 
    send_from = ''
    HOURS = 2

    # Connect to DB
    session = connect_to_db('localhost', 'sems', 'sems', 'sems')

    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=HOURS)

    found_transfers = session.query(TransferLog).\
            filter(TransferLog.ended >= hour_ago).\
            filter(TransferLog.name == "telus_network").\
            filter(TransferLog.status == "Complete").\
            filter(TransferLog.filename.endswith('.xml')).\
            all()

    for t in found_transfers:
        print '%s - %s' % (t.ended, os.path.basename(t.filename))

    if found_transfers:

        # Create message container
        # Supports HTML and TEXT emails
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = send_from
        msg['To'] = ','.join(send_to)

        # Email Templates
        # I know they suck and it should be changed, give me more time
        text = """
From: %s
To: %s
Subject: %s

Telus 2 Hour Report

This is an automated report, please do not reply.

The following assets were delivered:

""" % (send_from, ', '.join(send_to), subject)
    
        html = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" 
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<html>
  <head>
    <meta http-equiv="content-type" content="text/php; charset=utf-8" />
    <style type="text/css">
      .tftable {font-size:12px;color:#333333;width:100%;border-width: 1px;border-color: #ebab3a;border-collapse: collapse;}
      .tftable th {font-size:12px;background-color:#F57B20;border-width: 1px;padding: 8px;border-style: solid;border-color: #ebab3a;text-align:left;}
      .tftable tr {background-color:#ffffff;}
      .tftable td {font-size:12px;border-width: 1px;padding: 8px;border-style: solid;border-color: #ebab3a;}
      .tftable tr:hover {background-color:#ffff99;}
    </style>
  </head>

  <body>
    <a href="www.vubiquity.com"><img src="http://www.vubiquity.com/sites/default/files/logo.png" atl="Vubiquity"></a>
    <h2>Telus 2 Hour Report</h2>
    <p><em>This is an automated report, please do not reply.</em></p>
    <p>The following files were delivered:</p>
    
    <table class="tftable" border="1">
      <tr>
        <th>Time (UTC)</th>
        <th>Asset Name</th>
      </tr>\n
"""

        for t in found_transfers:
            filename =  os.path.splitext(os.path.basename(t.filename))[0]
            text += '%s - %s\n' % (t.ended, filename)
            html += '  <tr><td>%s</td><td>%s</td></tr>\n' % (t.ended, filename)

        html += """
    </table>
  </body>
</html>
"""

        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
     
        # Now send email
        server = smtplib.SMTP(mail_server)
        server.sendmail(send_from, send_to, msg.as_string())
        server.quit()
