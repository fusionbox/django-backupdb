"""
Adapted from http://djangosnippets.org/snippets/823/
"""
from optparse import make_option
from subprocess import Popen, PIPE
import glob
import os
import pipes

from django.core.management.base import BaseCommand, CommandError

from .backupdb import BACKUP_DIR


TIMESTAMP_PATTERN = '*-[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'


class RestoreError(Exception):
    pass


def get_latest_file(pattern):
    l = glob.glob(pattern)
    l.sort()
    l.reverse()

    if not l:
        raise CommandError('No backups found matching "{0}" pattern!'.format(pattern))

    return l[0]


def require_backup_exists(func):
    def new_func(self, **kwargs):
        backup_file = kwargs['backup_file']
        if not os.path.exists(backup_file):
            raise RestoreError(
                'Could not find file \'{0}\'!'.format(backup_file)
            )
        else:
            return func(self, **kwargs)
    return new_func


class Command(BaseCommand):
    help = 'Restores each database in settings.DATABASES from latest db backup.'
    can_import_settings = True

    option_list = BaseCommand.option_list + (
        make_option(
            '--backup-name',
            help='Backup to restore from e.g. "mybackup" in "mybackup.pgsql.gz".  Defaults to latest timestamped backup name.',
        ),
        make_option(
            '--drop-tables',
            action='store_true',
            default=False,
            help='Drop all tables in databases before restoring them',
        ),
    )

    def handle(self, *args, **options):
        from django.conf import settings

        if not os.path.exists(BACKUP_DIR):
            raise CommandError('Backup dir \'{0}\' does not exist!'.format(BACKUP_DIR))

        backup_name = options.get('backup_name')
        drop_tables = options.get('drop_tables')

        # Loop through databases and restore
        for database_name in settings.DATABASES:
            config = settings.DATABASES[database_name]

            # MySQL command and args
            if config['ENGINE'] == 'django.db.backends.mysql':
                restore_cmd = self.do_mysql_restore

                if backup_name:
                    backup_file = '{0}/{1}-{2}.mysql.gz'.format(BACKUP_DIR, database_name, backup_name)
                else:
                    backup_file = get_latest_file('{0}/{1}.mysql.gz'.format(BACKUP_DIR, TIMESTAMP_PATTERN))

                restore_kwargs = {
                    'backup_file': backup_file,
                    'db': config['NAME'],
                    'user': config.get('USER', None),
                    'password': config.get('PASSWORD', None),
                    'host': config.get('HOST', None),
                    'port': config.get('PORT', None),
                    'drop': drop_tables,
                }

            # PostgreSQL command and args
            elif config['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
                restore_cmd = self.do_postgresql_restore

                if backup_name:
                    backup_file = '{0}/{1}-{2}.pgsql.gz'.format(BACKUP_DIR, database_name, backup_name)
                else:
                    backup_file = get_latest_file('{0}/{1}.pgsql.gz'.format(BACKUP_DIR, TIMESTAMP_PATTERN))

                restore_kwargs = {
                    'backup_file': backup_file,
                    'db': config['NAME'],
                    'user': config.get('USER', None),
                    'password': config.get('PASSWORD', None),
                    'host': config.get('HOST', None),
                    'port': config.get('PORT', None),
                    'drop': drop_tables,
                }

            # SQLite command and args
            elif config['ENGINE'] == 'django.db.backends.sqlite3':
                restore_cmd = self.do_sqlite_restore

                if backup_name:
                    backup_file = '{0}/{1}-{2}.sqlite.gz'.format(BACKUP_DIR, database_name, backup_name)
                else:
                    backup_file = get_latest_file('{0}/{1}.sqlite.gz'.format(BACKUP_DIR, TIMESTAMP_PATTERN))

                restore_kwargs = {
                    'backup_file': backup_file,
                    'db_file': config['NAME'],
                }

            # Unsupported
            else:
                restore_cmd = None

            # Run restore command with args
            print '========== Restoring \'{0}\'...'.format(database_name)

            if restore_cmd:
                try:
                    restore_cmd(**restore_kwargs)
                    print '========== ...done!'
                except RestoreError as e:
                    print e.message
                    print '========== ...skipped.'
            else:
                print 'Restore for {0} engine not implemented.'.format(config['ENGINE'])
                print '========== ...skipped.'

            print ''

    @require_backup_exists
    def do_mysql_restore(self, backup_file, db, user, password=None, host=None, port=None, drop=False):
        # Build args to restore command
        restore_args = []
        restore_args += ['--user={0}'.format(pipes.quote(user))]
        if password:
            restore_args += ['--password={0}'.format(pipes.quote(password))]
        if host:
            restore_args += ['--host={0}'.format(pipes.quote(host))]
        if port:
            restore_args += ['--port={0}'.format(pipes.quote(port))]
        restore_args += [pipes.quote(db)]
        restore_args = ' '.join(restore_args)

        # Sanitize other args
        backup_file = pipes.quote(backup_file)

        # Build commands
        drop_cmd = 'mysqldump {restore_args} --no-data | grep "^DROP" | mysql {restore_args}'.format(
            restore_args=restore_args,
        )
        restore_cmd = 'cat {backup_file} | gunzip | mysql {restore_args}'.format(
            drop_cmd=drop_cmd,
            backup_file=backup_file,
            restore_args=restore_args,
        )

        # Execute
        if drop:
            import pdb; pdb.set_trace()
            self.do_command(drop_cmd, 'clearing', db)
        self.do_command(restore_cmd, 'restoring', db)

    @require_backup_exists
    def do_postgresql_restore(self, backup_file, db, user, password=None, host=None, port=None, drop=False):
        # Build args to restore command
        restore_args = []
        restore_args += ['--username={0}'.format(pipes.quote(user))]
        if host:
            restore_args += ['--host={0}'.format(pipes.quote(host))]
        if port:
            restore_args += ['--port={0}'.format(pipes.quote(port))]
        restore_args += [pipes.quote(db)]
        restore_args = ' '.join(restore_args)

        pgpassword_env = 'PGPASSWORD={0} '.format(password) if password else ''

        # Sanitize other args
        backup_file = pipes.quote(backup_file)

        # Build commands
        drop_sql = '"SELECT \'DROP TABLE IF EXISTS \\"\' || tablename || \'\\" CASCADE;\' FROM pg_tables WHERE schemaname = \'public\';"'
        drop_cmd = '{pgpassword_env}psql {restore_args} -t -c {drop_sql} | {pgpassword_env}psql {restore_args}'.format(
            pgpassword_env=pgpassword_env,
            restore_args=restore_args,
            drop_sql=drop_sql,
        )
        restore_cmd = 'cat {backup_file} | gunzip | {pgpassword_env}psql {restore_args}'.format(
            backup_file=backup_file,
            pgpassword_env=pgpassword_env,
            restore_args=restore_args,
        )

        # Execute
        if drop:
            import pdb; pdb.set_trace()
            self.do_command(drop_cmd, 'dropping', db)
        self.do_command(restore_cmd, 'restoring', db)

    @require_backup_exists
    def do_sqlite_restore(self, backup_file, db_file):
        # Build filenames
        db_file = pipes.quote(db_file)
        backup_file = pipes.quote(backup_file)

        # Build command
        cmd = 'cat {backup_file} | gunzip > {db_file}'.format(
            backup_file=backup_file,
            db_file=db_file,
        )

        # Execute
        self.do_command(cmd, 'restoring', db_file)

    def do_command(cls, cmd, verb, db):
        """
        Executes a command and prints a status message.
        """
        print '{0} database...executing:'.format(verb.capitalize())
        print cmd

        with open('/dev/null', 'w') as FNULL:
            process = Popen(cmd, stdin=PIPE, stdout=FNULL, stderr=FNULL, shell=True)
            process.wait()

            if process.returncode != 0:
                raise RestoreError('Error code {code} while {verb} database \'{db}\'!'.format(
                    code=process.returncode,
                    verb=verb,
                    db=db,
                ))
