import os

from django.conf import settings

from backupdb.backends.mysql import MySQLBackend
from backupdb.backends.sqlite import SQLite3Backend
from backupdb.backends.postgresql import PostgreSQLBackend


DEFAULT_BACKUP_DIR = 'backups'

BACKUP_CONFIG = {
    'django.db.backends.mysql': MySQLBackend,
    'django.db.backends.postgresql_psycopg2': PostgreSQLBackend,
    'django.contrib.gis.db.backends.postgis': PostgreSQLBackend,
    'django.db.backends.sqlite3': SQLite3Backend,
}


def get_backup_directory():
    return os.path.abspath(
        getattr(settings, 'BACKUPDB_DIRECTORY', DEFAULT_BACKUP_DIR))
