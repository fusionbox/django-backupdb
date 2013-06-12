#!/bin/sh
python setup.py nosetests --with-coverage --cover-package=backupdb,backupdb_utils --cover-erase $@
