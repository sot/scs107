# Set the task name
TASK = scs107

# Uncomment the correct choice indicating either SKA or TST flight environment
FLIGHT_ENV = SKA

BIN = 
SHARE = scs107_response.py 
DATA = task_schedule.cfg
DOC = 

include /proj/sot/ska/include/Makefile.FLIGHT


install:
#  Uncomment the lines which apply for this task
#	mkdir -p $(INSTALL_BIN)
	mkdir -p $(INSTALL_DATA)
	mkdir -p $(INSTALL_SHARE)
#	mkdir -p $(INSTALL_DOC)
#	mkdir -p $(INSTALL_LIB)
#	rsync --times --cvs-exclude $(BIN) $(INSTALL_BIN)/
	rsync --times --cvs-exclude $(DATA) $(INSTALL_DATA)/
	rsync --times --cvs-exclude $(SHARE) $(INSTALL_SHARE)/
#	rsync --times --cvs-exclude $(DOC) $(INSTALL_DOC)/
#	rsync --times --cvs-exclude $(LIB) $(INSTALL_LIB)/
#	pod2html task.pl > $(INSTALL_DOC)/task.html
