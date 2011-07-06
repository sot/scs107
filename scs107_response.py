#!/usr/bin/env python

import os
import re
import logging
from logging.handlers import SMTPHandler

def scs107_cmds(comm_time, disarm_file):
    return """
An SCS107 has been detected at or before %(comm_time)s
Please update command states and turn off this warning.

Procedure:
-----

# Check for the presence of the disarm file.  If already there and
# the date / owner implies someone else is doing the update then stop.
ls -l %(disarm)s

# Disable further SCS107 reminders and check ownership:
touch %(disarm)s
chgrp aspect %(disarm)s
chmod g+w %(disarm)s
ls -l %(disarm)s

# clone the cmd_states project
mkdir /pool1/scs107
cd /pool1/scs107
hg clone /proj/sot/ska/hg/cmd_states
cd cmd_states

# confirm that the nonload_cmds_archive.py is aspect writeable
chgrp aspect nonload_cmds_archive.py
chmod g+w nonload_cmds_archive.py

# change to aca user
su aca

# Set the SCS107 time (from telecon email report) as a variable
# example: set scs107time='2011:158:15:23:10.000'
set scs107time='<SCS107 time>'

# Run add_nonload_cmds.py
# (after SOSA transition, add --observing-only flag to this)

/proj/sot/ska/bin/python ./add_nonload_cmds.py --dbi sybase --server sybase \\
                              --user aca_ops --database aca \\
                              --date ${scs107time} \\
                              --cmd-set scs107 --interrupt \\
                              --archive-file nonload_cmds_archive.py

# stop working as aca
<CTRL>-d

# Commit the changes to nonload_cmds_archive.py
hg commit nonload_cmds_archive.py \\
   -m "updated nonload cmds for scs107 before %(comm_time)s" \\
hg push 

-----
End Procedure

Documentation for add_nonload_cmds.py at:
( http://cxc.harvard.edu/mta/ASPECT/tool_doc/cmd_states/add_nonload_cmds.html )
""" % { 'comm_time' : comm_time, 'disarm': disarm_file } 



log = logging.getLogger()
log.setLevel(logging.DEBUG)
# emails...
smtp_handler = logging.handlers.SMTPHandler('localhost',
                                            'aca@head.cfa.harvard.edu',
                                            'aca@head.cfa.harvard.edu',
                                            'scs107 reminder')

smtp_handler.setLevel(logging.INFO)
log.addHandler(smtp_handler)

disarm_file = os.path.join(os.environ['SKA_DATA'], 'scs107', 'disarm')
arc_hist_file = os.path.join(os.environ['SKA_DATA'], 'arc', 'SCS107_history')

      
arc_history = open(arc_hist_file).readlines()
state = arc_history[-1].rstrip()
line_match = re.match('(\d{4}:\d{3}:\d{2}:\d{2}:\d{2})\s::\s(Loads\srunning|SCS107\sdetected)', state)
if not line_match:
    raise ValueError("Unexpected string '%s' found in %s" % (state, arc_hist_file))
if line_match.group(2) == 'SCS107 detected':
    if not os.path.exists(disarm_file):
        cmds = scs107_cmds(line_match.group(1), disarm_file)
        log.info(cmds)
if line_match.group(2) == 'Loads running':
    if os.path.exists(disarm_file):
        os.unlink(disarm_file)

log.removeHandler(smtp_handler)
    
