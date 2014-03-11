import atexit
import dj_database_url
import os
import shutil
import tempfile

DEBUG = True

DATABASE = {
    'default': dj_database_url.config(default='sqlite://:memory:'),
}

INSTALLED_APPS = (
    'backupdb',
    'backupdb.tests.app',
)

SECRET_KEY = 'this is a secret!'

BACKUPDB_DIRECTORY = tempfile.mkdtemp()

# Cleanup after itself
atexit.register(shutil.rmtree, BACKUPDB_DIRECTORY)
