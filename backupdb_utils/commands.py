import glob
import os
import shlex

from backupdb_utils.exceptions import RestoreError
from backupdb_utils.processtools import pipe_commands_to_file
from backupdb_utils.settings import BACKUP_DIR, TIMESTAMP_PATTERN


def get_latest_timestamped_file(ext):
    """
    Gets the latest timestamped backup file name with the given database type
    extension.
    """
    # Make glob pattern
    pattern = '{dir}/{pattern}.{ext}.gz'.format(
        dir=BACKUP_DIR,
        pattern=TIMESTAMP_PATTERN,
        ext=ext,
    )

    # Find files
    l = glob.glob(pattern)
    l.sort()
    l.reverse()

    if not l:
        raise RestoreError('No backups found matching "{0}" pattern!'.format(pattern))

    return l[0]


def require_backup_exists(func):
    """
    Requires that the file referred to by the `backup_file` argument exists in
    the file system before running the decorated function.
    """
    def new_func(*args, **kwargs):
        backup_file = kwargs['backup_file']
        if not os.path.exists(backup_file):
            raise RestoreError('Could not find file \'{0}\'!'.format(backup_file))
        return func(*args, **kwargs)
    return new_func


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


@require_backup_exists
def do_mysql_restore(backup_file, db, user, password=None, host=None, port=None, drop=False):
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
        self.do_command(drop_cmd, 'clearing', db)
    self.do_command(restore_cmd, 'restoring', db)


@require_backup_exists
def do_postgresql_restore(backup_file, db, user, password=None, host=None, port=None, drop=False):
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
        self.do_command(drop_cmd, 'dropping', db)
    self.do_command(restore_cmd, 'restoring', db)


@require_backup_exists
def do_sqlite_restore(backup_file, db_config):
    db_file = db_config['NAME']

    cmd = ['cat', backup_file]
    pipe_commands_to_file([cmd, ['gunzip']], path=db_file)


ENGINE_OPTIONS = {
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
