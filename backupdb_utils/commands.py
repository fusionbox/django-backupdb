import logging
import os
import shlex

from django.core.management.base import BaseCommand

from .exceptions import RestoreError
from .processes import pipe_commands, pipe_commands_to_file


PG_DROP_SQL = """SELECT 'DROP TABLE IF EXISTS "' || tablename || '" CASCADE;' FROM pg_tables WHERE schemaname = 'public';"""


class BaseBackupDbCommand(BaseCommand):
    can_import_settings = True

    LOG_LEVELS = {
        0: logging.ERROR,
        1: logging.INFO,
        2: logging.DEBUG,
        3: logging.DEBUG,
    }
    LOG_FORMAT = '%(asctime)s - %(levelname)-8s: %(message)s'

    def _setup_logging(self, level):
        level = int(level)
        logging.basicConfig(format=self.LOG_FORMAT, level=self.LOG_LEVELS[level])

    def handle(self, *args, **options):
        self._setup_logging(options['verbosity'])


def apply_arg_values(arg_values):
    """
    Apply argument to values.

    l = [('--name={0}', 'name'),
         ('--password={0}', 'password'),
         ('--level={0}', ''),
         ('--last={0}', None)]
    assert apply_arg_values(l) == ['--name=name', '--password=password']
    """
    return [a.format(v) for a, v in arg_values if v]


def require_backup_exists(func):
    """
    Requires that the file referred to by `backup_file` exists in the file
    system before running the decorated function.
    """
    def new_func(*args, **kwargs):
        backup_file = kwargs['backup_file']
        if not os.path.exists(backup_file):
            raise RestoreError("Could not find file '{0}'".format(backup_file))
        return func(*args, **kwargs)
    return new_func


def get_mysql_args(db_config):
    """
    Returns an array of argument values that will be passed to a `mysql` or
    `mysqldump` process when it is started based on the given database
    configuration.
    """
    db = db_config['NAME']

    mapping = [('--user={0}', db_config.get('USER')),
               ('--password={0}', db_config.get('PASSWORD')),
               ('--host={0}', db_config.get('HOST')),
               ('--port={0}', db_config.get('PORT'))]
    args = apply_arg_values(mapping)
    args.append(db)

    return args


def get_postgresql_args(db_config, extra_args=None):
    """
    Returns an array of argument values that will be passed to a `psql` or
    `pg_dump` process when it is started based on the given database
    configuration.
    """
    db = db_config['NAME']

    mapping = [('--username={0}', db_config.get('USER')),
               ('--host={0}', db_config.get('HOST')),
               ('--port={0}', db_config.get('PORT'))]
    args = apply_arg_values(mapping)

    if extra_args is not None:
        args.extend(shlex.split(extra_args))
    args.append(db)

    return args


def get_postgresql_env(db_config):
    """
    Returns a dict containing extra environment variable values that will be
    added to the environment of the `psql` or `pg_dump` process when it is
    started based on the given database configuration.
    """
    password = db_config.get('PASSWORD')
    return {'PGPASSWORD': password} if password else None


def do_mysql_backup(backup_file, db_config, show_output=False):
    args = get_mysql_args(db_config)

    cmd = ['mysqldump'] + args
    pipe_commands_to_file([cmd, ['gzip']], path=backup_file, show_stderr=show_output)


def do_postgresql_backup(backup_file, db_config, pg_dump_options=None, show_output=False):
    env = get_postgresql_env(db_config)
    args = get_postgresql_args(db_config, pg_dump_options)

    cmd = ['pg_dump', '--clean'] + args
    pipe_commands_to_file([cmd, ['gzip']], path=backup_file, extra_env=env, show_stderr=show_output)


def do_sqlite_backup(backup_file, db_config, show_output=False):
    db_file = db_config['NAME']

    cmd = ['cat', db_file]
    pipe_commands_to_file([cmd, ['gzip']], path=backup_file, show_stderr=show_output)


@require_backup_exists
def do_mysql_restore(backup_file, db_config, drop_tables=False, show_output=False):
    args = get_mysql_args(db_config)
    mysql_cmd = ['mysql'] + args

    kwargs = {'show_stderr': show_output, 'show_last_stdout': show_output}

    if drop_tables:
        dump_cmd = ['mysqldump'] + args + ['--no-data']
        pipe_commands([dump_cmd, ['grep', '^DROP'], mysql_cmd], **kwargs)

    pipe_commands([['cat', backup_file], ['gunzip'], mysql_cmd], **kwargs)


@require_backup_exists
def do_postgresql_restore(backup_file, db_config, drop_tables=False, show_output=False):
    env = get_postgresql_env(db_config)
    args = get_postgresql_args(db_config)
    psql_cmd = ['psql'] + args

    kwargs = {'extra_env': env, 'show_stderr': show_output, 'show_last_stdout': show_output}

    if drop_tables:
        gen_drop_sql_cmd = psql_cmd + ['-t', '-c', PG_DROP_SQL]
        pipe_commands([gen_drop_sql_cmd, psql_cmd], **kwargs)

    pipe_commands([['cat', backup_file], ['gunzip'], psql_cmd], **kwargs)


@require_backup_exists
def do_sqlite_restore(backup_file, db_config, drop_tables=False, show_output=False):
    db_file = db_config['NAME']

    cmd = ['cat', backup_file]
    pipe_commands_to_file([cmd, ['gunzip']], path=db_file, show_stderr=show_output)
