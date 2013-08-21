#!/bin/sh

python setup.py nosetests \
  --exclude="^backupdb" \
  --with-coverage \
  --cover-package=backupdb_utils \
  --cover-erase $@
