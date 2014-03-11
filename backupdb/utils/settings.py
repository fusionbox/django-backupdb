from .commands import (
    do_mysql_backup,
    do_mysql_restore,
    do_postgresql_backup,
    do_postgresql_restore,
    do_sqlite_backup,
    do_sqlite_restore,
)
from django.conf import settings


DEFAULT_BACKUP_DIR = 'backups'
BACKUP_DIR = getattr(settings, 'BACKUPDB_DIRECTORY', DEFAULT_BACKUP_DIR)
BACKUP_TIMESTAMP_PATTERN = '*-[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
BACKUP_CONFIG = {
    'django.db.backends.mysql': {
        'backup_extension': 'mysql',
        'backup_func': do_mysql_backup,
        'restore_func': do_mysql_restore,
    },
    'django.db.backends.postgresql_psycopg2': {
        'backup_extension': 'pgsql',
        'backup_func': do_postgresql_backup,
        'restore_func': do_postgresql_restore,
    },
    'django.contrib.gis.db.backends.postgis': {
        'backup_extension': 'pgsql',
        'backup_func': do_postgresql_backup,
        'restore_func': do_postgresql_restore,
    },
    'django.db.backends.sqlite3': {
        'backup_extension': 'sqlite',
        'backup_func': do_sqlite_backup,
        'restore_func': do_sqlite_restore,
    },
}
