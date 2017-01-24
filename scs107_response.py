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

# Check for heart attack on timelines cron task
# if it exists, don't proceed with this process until that
# is understood
ls -l /proj/sot/ska/data/timelines/task_sched_heart_attack

# Stop timelines cron task
touch /proj/sot/ska/data/timelines/task_sched_heart_attack

# Backup the flight databases
cd /proj/sot/ska/data/sybase_backup
./dump_cmd_tables.sh

# clone the cmd_states project from either github or clone in ~/git
# (if cloning from ~/git, make sure you're working from an updated clone)
mkdir /pool1/scs107
cd /pool1/scs107
git clone git@github.com:sot/cmd_states.git
cd cmd_states

# confirm that the nonload_cmds_archive.py is aspect writeable
chgrp aspect nonload_cmds_archive.py
chmod g+w nonload_cmds_archive.py

# Set the SCS107 time (from telecon email report) as a variable
# example: setenv scs107time '2011:158:15:23:10.000'
# (use of 'setenv' below expects tcsh)
setenv scs107time '<SCS107 time>'

# change to aca user
su aca

# Run add_nonload_cmds.py.  If only observing loads should be interrupted,
# use --observing-only flag as demonstrated below.

/proj/sot/ska/bin/python ./add_nonload_cmds.py --dbi sybase --server sybase \\
                              --user aca_ops --database aca \\
                              --date ${scs107time} \\
                              --cmd-set scs107 --interrupt \\
                              --observing-only \\
                              --archive-file nonload_cmds_archive.py

# Add the cmds to the sqlite version of the table too, but don't archive again to
# nonload_cmds_archive.py.  Set a bogus/not_used file instead for that operation.

/proj/sot/ska/bin/python ./add_nonload_cmds.py --dbi sqlite \\
                              --server /proj/sot/ska/data/cmd_states/cmd_states.db3 \\
                              --date ${scs107time} \\
                              --cmd-set scs107 --interrupt \\
                              --observing-only \\
                              --archive-file not_used.py

# stop working as aca
<CTRL>-d

# Commit the changes to nonload_cmds_archive.py
git commit nonload_cmds_archive.py \\
   -m "Update nonload cmds for SCS107 at ${scs107time}"
git push origin

# Remove timelines heart attack
rm /proj/sot/ska/data/timelines/task_sched_heart_attack

# Get out of the /pool1/scs107 directory
cd

# Delete the cmd_states clone
rm -rf /pool1/scs107

-----
End Procedure

Documentation for add_nonload_cmds.py at:
( http://cxc.harvard.edu/mta/ASPECT/tool_doc/cmd_states/add_nonload_cmds.html )
""" % {'comm_time': comm_time, 'disarm': disarm_file}

log = logging.getLogger()
log.setLevel(logging.DEBUG)

disarm_file = os.path.join(os.environ['SKA_DATA'], 'scs107', 'disarm')
arc_hist_file = os.path.join(os.environ['SKA_DATA'], 'arc', 'SCS107_history')
arc_history = open(arc_hist_file).readlines()
state = arc_history[-1].rstrip()
line_match = re.match(
    '(\d{4}:\d{3}:\d{2}:\d{2}:\d{2})\s::\s(Loads\srunning|SCS107\sdetected)',
    state)
if not line_match:
    raise ValueError(
        "Unexpected string '%s' found in %s" % (state, arc_hist_file))
if line_match.group(2) == 'SCS107 detected':
    if not os.path.exists(disarm_file):
        comm_time = line_match.group(1)
        cmds = scs107_cmds(comm_time, disarm_file)
        # emails...
        smtp_handler = SMTPHandler('localhost',
                                   'aca@head.cfa.harvard.edu',
                                   'aca@head.cfa.harvard.edu',
                                   'SCS107 cmd_states reminder (alert from %s)'
                                   % comm_time)
        smtp_handler.setLevel(logging.INFO)
        log.addHandler(smtp_handler)
        log.info(cmds)
        log.removeHandler(smtp_handler)
if line_match.group(2) == 'Loads running':
    if os.path.exists(disarm_file):
        os.unlink(disarm_file)
