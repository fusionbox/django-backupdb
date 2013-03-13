"""
Adapted from http://djangosnippets.org/snippets/823/
"""

from optparse import make_option
from subprocess import Popen, PIPE
import os
import pipes
import time

from django.core.management.base import BaseCommand

BACKUP_DIR = 'backups'


class BackupError(Exception):
    pass


class Command(BaseCommand):
    help = 'Backs up each database in settings.DATABASES.'
    can_import_settings = True

    option_list = BaseCommand.option_list + (
        make_option(
            '--backup-name',
            help='Specify a name for the backup.  Defaults to the current timestamp.  Example: `--backup-name=test` will create backup files that look like "test.pgsql.gz".',
        ),
        make_option(
            '--pg-dump-options',
            help='For postgres backups, a list of additional options that will be passed through to the pg_dump utility.  Example: `--pg-dump-options="--inserts --no-owner"`',
        ),
    )

    def handle(self, *args, **options):
        from django.conf import settings

        current_time = time.strftime('%F-%s')

        backup_name = options.get('backup_name')
        pg_dump_options = options.get('pg_dump_options')

        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        # Loop through databases and backup
        for database_name in settings.DATABASES:
            config = settings.DATABASES[database_name]

            backup_kwargs = {
                'db': config['NAME'],
                'user': config['USER'],
                'password': config.get('PASSWORD', None),
                'host': config.get('HOST', None),
                'port': config.get('PORT', None),
            }

            # MySQL command and args
            if config['ENGINE'] == 'django.db.backends.mysql':
                backup_cmd = self.do_mysql_backup

                if backup_name:
                    backup_file = '{0}-{1}.mysql.gz'.format(database_name, backup_name)
                else:
                    backup_file = '{0}-{1}.mysql.gz'.format(database_name, current_time)

                backup_kwargs['backup_file'] = os.path.join(BACKUP_DIR, backup_file)

            # PostgreSQL command and args
            elif config['ENGINE'] in ('django.db.backends.postgresql_psycopg2', 'django.contrib.gis.db.backends.postgis'):
                backup_cmd = self.do_postgresql_backup

                if backup_name:
                    backup_file = '{0}-{1}.pgsql.gz'.format(database_name, backup_name)
                else:
                    backup_file = '{0}-{1}.pgsql.gz'.format(database_name, current_time)

                backup_kwargs['backup_file'] = os.path.join(BACKUP_DIR, backup_file)
                backup_kwargs['pg_dump_options'] = pg_dump_options

            # SQLite command and args
            elif config['ENGINE'] == 'django.db.backends.sqlite3':
                backup_cmd = self.do_sqlite_backup

                if backup_name:
                    backup_file = '{0}-{1}.sqlite.gz'.format(database_name, backup_name)
                else:
                    backup_file = '{0}-{1}.sqlite.gz'.format(database_name, current_time)

                backup_kwargs = {
                    'backup_file': os.path.join(BACKUP_DIR, backup_file),
                    'db_file': config['NAME'],
                }

            # Unsupported
            else:
                backup_cmd = None

            # Run backup command with args
            print '========== Backing up \'{0}\'...'.format(database_name)

            if backup_cmd:
                try:
                    backup_cmd(**backup_kwargs)
                    print '========== ...done!'
                except BackupError as e:
                    print e.message
                    print '========== ...skipped.'
            else:
                print 'Backup for {0} engine not implemented.'.format(config['ENGINE'])
                print '========== ...skipped.'

            print ''

    def do_mysql_backup(self, backup_file, db, user, password=None, host=None, port=None):
        # Build args to dump command
        dump_args = []
        dump_args += ['--user={0}'.format(pipes.quote(user))]
        if password:
            dump_args += ['--password={0}'.format(pipes.quote(password))]
        if host:
            dump_args += ['--host={0}'.format(pipes.quote(host))]
        if port:
            dump_args += ['--port={0}'.format(pipes.quote(port))]
        dump_args += [pipes.quote(db)]
        dump_args = ' '.join(dump_args)

        # Build filenames
        backup_file = pipes.quote(backup_file)

        # Build command
        cmd = 'mysqldump {dump_args} | gzip > {backup_file}'.format(
            dump_args=dump_args,
            backup_file=backup_file,
        )

        # Execute
        self.do_command(cmd, db)

        print 'Backed up {db}; Load with `cat {backup_file} | gunzip | mysql {dump_args}`'.format(
            db=db,
            backup_file=backup_file,
            dump_args=dump_args,
        )

    def do_postgresql_backup(self, backup_file, db, user, password=None, host=None, port=None, pg_dump_options=None):
        # Build args to dump command
        dump_args = ['--clean']
        if pg_dump_options:
            dump_args += [pg_dump_options]
        dump_args += ['--username={0}'.format(pipes.quote(user))]
        if host:
            dump_args += ['--host={0}'.format(pipes.quote(host))]
        if port:
            dump_args += ['--port={0}'.format(pipes.quote(port))]
        dump_args += [pipes.quote(db)]
        dump_args = ' '.join(dump_args)

        pgpassword_env = 'PGPASSWORD={0} '.format(password) if password else ''

        # Build filenames
        backup_file = pipes.quote(backup_file)

        # Build command
        cmd = '{pgpassword_env}pg_dump {dump_args} | gzip > {backup_file}'.format(
            pgpassword_env=pgpassword_env,
            dump_args=dump_args,
            backup_file=backup_file,
        )

        # Execute
        self.do_command(cmd, db)

        print 'Backed up {db}; Load with `cat {backup_file} | gunzip | psql {dump_args}`'.format(
            db=db,
            backup_file=backup_file,
            dump_args=dump_args,
        )

    def do_sqlite_backup(self, backup_file, db_file):
        # Build filenames
        db_file = pipes.quote(db_file)
        backup_file = pipes.quote(backup_file)

        # Build command
        cmd = 'gzip < {db_file} > {backup_file}'.format(
            db_file=db_file,
            backup_file=backup_file,
        )

        # Execute
        self.do_command(cmd, db_file)

        print 'Backed up {db_file}; Load with `cat {backup_file} | gunzip > {db_file}`'.format(
            db_file=db_file,
            backup_file=backup_file,
        )

    def do_command(cls, cmd, db):
        """
        Executes a command and prints a status message.
        """
        print 'executing:'
        print cmd

        with open('/dev/null', 'w') as FNULL:
            process = Popen(cmd, stdin=PIPE, stdout=FNULL, stderr=FNULL, shell=True)
            process.wait()

            if process.returncode != 0:
                raise BackupError('Error code {code} while backing up database \'{db}\'!'.format(
                    code=process.returncode,
                    db=db,
                ))
