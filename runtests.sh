#!/bin/sh

python setup.py nosetests --exclude="^backupdb" $@
