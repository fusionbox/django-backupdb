import os
import shlex

from .exceptions import RestoreError
from .processes import pipe_commands, pipe_commands_to_file


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


def do_mysql_backup(backup_file, db_config, show_output=False):
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

    pipe_commands_to_file([cmd, ['gzip']], path=backup_file, show_stderr=show_output)


def do_postgresql_backup(backup_file, db_config, pg_dump_options=None, show_output=False):
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

    env = {'PGPASSWORD': password} if password else None
    pipe_commands_to_file([cmd, ['gzip']], path=backup_file, extra_env=env, show_stderr=show_output)


def do_sqlite_backup(backup_file, db_config, show_output=False):
    db_file = db_config['NAME']

    cmd = ['cat', db_file]
    pipe_commands_to_file([cmd, ['gzip']], path=backup_file, show_stderr=show_output)


@require_backup_exists
def do_mysql_restore(backup_file, db_config, drop_tables=False, show_output=False):
    db = db_config['NAME']
    user = db_config['USER']
    password = db_config.get('PASSWORD')
    host = db_config.get('HOST')
    port = db_config.get('PORT')

    cmd_args = ['--user={0}'.format(user)]
    if password:
        cmd_args += ['--password={0}'.format(password)]
    if host:
        cmd_args += ['--host={0}'.format(host)]
    if port:
        cmd_args += ['--port={0}'.format(port)]
    cmd_args += [db]

    dump_cmd = ['mysqldump'] + cmd_args + ['--no-data']
    mysql_cmd = ['mysql'] + cmd_args

    kwargs = {'show_stderr': show_output, 'show_last_stdout': show_output}

    if drop_tables:
        pipe_commands([dump_cmd, ['grep', '^DROP'], mysql_cmd], **kwargs)
    pipe_commands([['cat', backup_file], ['gunzip'], mysql_cmd], **kwargs)


@require_backup_exists
def do_postgresql_restore(backup_file, db_config, drop_tables=False, show_output=False):
    db = db_config['NAME']
    user = db_config['USER']
    password = db_config.get('PASSWORD')
    host = db_config.get('HOST')
    port = db_config.get('PORT')

    cmd_args = ['--username={0}'.format(user)]
    if host:
        cmd_args += ['--host={0}'.format(host)]
    if port:
        cmd_args += ['--port={0}'.format(port)]
    cmd_args += [db]

    drop_sql = "SELECT 'DROP TABLE IF EXISTS \"' || tablename || '\" CASCADE;' FROM pg_tables WHERE schemaname = 'public';"

    psql_cmd = ['psql'] + cmd_args
    gen_drop_sql_cmd = psql_cmd + ['-t', '-c', drop_sql]

    env = {'PGPASSWORD': password} if password else None
    kwargs = {'extra_env': env, 'show_stderr': show_output, 'show_last_stdout': show_output}

    if drop_tables:
        pipe_commands([gen_drop_sql_cmd, psql_cmd], **kwargs)
    pipe_commands([['cat', backup_file], ['gunzip'], psql_cmd], **kwargs)


@require_backup_exists
def do_sqlite_restore(backup_file, db_config, drop_tables=False, show_output=False):
    db_file = db_config['NAME']

    cmd = ['cat', backup_file]
    pipe_commands_to_file([cmd, ['gunzip']], path=db_file, show_stderr=show_output)
