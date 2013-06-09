"""
Adapted from http://djangosnippets.org/snippets/823/
"""
from optparse import make_option
from subprocess import CalledProcessError
import os
import shlex
import time

from django.core.management.base import BaseCommand

from backupdb_utils.processtools import pipe_commands_to_file
from backupdb_utils.streamtools import err, section, SectionError, set_verbosity


def do_mysql_backup(backup_file, db_config):
    db = db_config['NAME']
    user = db_config['USER']
    password = db_config.get('PASSWORD')
    host = db_config.get('HOST')
    port = db_config.get('PORT')

    cmd = ['mysqldump', '--user={0}'.format(user)]
    if password:
        cmd += ['--password={0}'.format(password)]
    if host:
        cmd += ['--host={0}'.format(host)]
    if port:
        cmd += ['--port={0}'.format(port)]
    cmd += [db]

    pipe_commands_to_file([cmd, ['gzip']], path=backup_file)


def do_postgresql_backup(backup_file, db_config, pg_dump_options=None):
    db = db_config['NAME']
    user = db_config['USER']
    password = db_config.get('PASSWORD')
    host = db_config.get('HOST')
    port = db_config.get('PORT')

    cmd = ['pg_dump', '--clean', '--username={0}'.format(user)]
    if host:
        cmd += ['--host={0}'.format(host)]
    if port:
        cmd += ['--port={0}'.format(port)]
    if pg_dump_options:
        cmd += shlex.split(pg_dump_options)
    cmd += [db]

    env = {'PGPASSWORD': password}
    pipe_commands_to_file([cmd, ['gzip']], path=backup_file, extra_env=env)


def do_sqlite_backup(backup_file, db_config):
    db_file = db_config['NAME']

    cmd = ['cat', db_file]
    pipe_commands_to_file([cmd, ['gzip']], path=backup_file)


BACKUP_DIR = 'backups'

ENGINE_OPTIONS = {
    'django.db.backends.mysql': {
        'backup_extension': 'mysql',
        'backup_func': do_mysql_backup,
    },
    'django.db.backends.postgresql_psycopg2': {
        'backup_extension': 'pgsql',
        'backup_func': do_postgresql_backup,
    },
    'django.contrib.gis.db.backends.postgis': {
        'backup_extension': 'pgsql',
        'backup_func': do_postgresql_backup,
    },
    'django.db.backends.sqlite3': {
        'backup_extension': 'sqlite',
        'backup_func': do_sqlite_backup,
    },
}


class BackupError(Exception):
    pass


class Command(BaseCommand):
    help = 'Backs up each database in settings.DATABASES.'
    can_import_settings = True

    option_list = BaseCommand.option_list + (
        make_option(
            '--backup-name',
            help=(
                'Specify a name for the backup.  Defaults to the current '
                'timestamp.  Example: `--backup-name=test` will create backup '
                'files that look like "default-test.pgsql.gz".'
            ),
        ),
        make_option(
            '--pg-dump-options',
            help=(
                'For postgres backups, a list of additional options that will '
                'be passed through to the pg_dump utility.  Example: '
                '`--pg-dump-options="--inserts --no-owner"`'
            ),
        ),
    )

    def handle(self, *args, **options):
        from django.conf import settings

        current_time = time.strftime('%F-%s')
        backup_name = options['backup_name'] or current_time

        set_verbosity(int(options['verbosity']))

        # Ensure backup dir present
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        # Loop through databases
        for db_name, db_config in settings.DATABASES.items():
            with section("Backing up '{0}'...".format(db_name)):
                # Get options for this engine type
                engine = db_config['ENGINE']
                engine_options = ENGINE_OPTIONS.get(engine)
                if not engine_options:
                    raise SectionError("! Backup for '{0}' engine not implemented".format(engine))

                # Create backup file name
                backup_base_name = '{db_name}-{backup_name}.{backup_extension}.gz'.format(
                    db_name=db_name,
                    backup_name=backup_name,
                    backup_extension=engine_options['backup_extension'],
                )
                backup_file = os.path.join(BACKUP_DIR, backup_base_name)

                # Find and backup command and get kwargs
                backup_func = engine_options['backup_func']
                backup_kwargs = {'backup_file': backup_file, 'db_config': db_config}
                if backup_func is do_postgresql_backup:
                    backup_kwargs['pg_dump_options'] = options['pg_dump_options']

                # Run backup command
                try:
                    backup_func(**backup_kwargs)
                    err("* Backup of '{db}' saved in '{backup_file}'".format(
                        db=db_name,
                        backup_file=backup_file))
                except (BackupError, CalledProcessError) as e:
                    raise SectionError('! ' + e.message)
