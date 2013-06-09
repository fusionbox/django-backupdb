"""
Adapted from http://djangosnippets.org/snippets/823/
"""
from optparse import make_option
from subprocess import Popen, PIPE
import os
import pipes
import shlex
import time
import sys

from django.core.management.base import BaseCommand


def do_mysql_backup(backup_file, db_config):
    db = db_config['NAME']
    user = db_config['USER']
    password = db_config.get('PASSWORD')
    host = db_config.get('HOST')
    port = db_config.get('PORT')

    # Build args to dump command
    args = []
    args += ['--user={0}'.format(pipes.quote(user))]
    if password:
        args += ['--password={0}'.format(pipes.quote(password))]
    if host:
        args += ['--host={0}'.format(pipes.quote(host))]
    if port:
        args += ['--port={0}'.format(pipes.quote(port))]
    args += [pipes.quote(db)]
    args = ' '.join(args)

    # Build filename
    backup_file = pipes.quote(backup_file)

    # Build command
    cmd = 'mysqldump {args} | gzip > {backup_file}'.format(
        args=args,
        backup_file=backup_file,
    )

    # Execute
    do_command(cmd, db)

    print 'Backed up {db}; Load with `cat {backup_file} | gunzip | mysql {args}`'.format(
        db=db,
        backup_file=backup_file,
        args=args,
    )


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
    # Build filenames
    backup_file = pipes.quote(backup_file)
    db_file = pipes.quote(db_config['NAME'])

    # Build command
    cmd = 'gzip < {db_file} > {backup_file}'.format(
        db_file=db_file,
        backup_file=backup_file,
    )

    # Execute
    do_command(cmd, db_file)

    print 'Backed up {db_file}; Load with `cat {backup_file} | gunzip > {db_file}`'.format(
        db_file=db_file,
        backup_file=backup_file,
    )


def do_command(cmd, db):
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


def pipe_commands_to_file(cmds, path, extra_env=None):
    """
    Executes the list of commands piping each one into the next and writing
    stdout of the last process into a file at the given path.
    """
    if extra_env:
        env = os.environ.copy()
        env.update(extra_env)
        env_str = ' '.join("{0}='{1}'".format(k, v) for k, v in extra_env.items()) + ' '
    else:
        env = None
        env_str = ''

    cmd_strs = [
        '{env_str}{cmd_str}'.format(env_str=env_str, cmd_str=' '.join(cmd))
        for cmd in cmds
    ]

    sys.stderr.write('Saving output of:\n')
    sys.stderr.write(' | '.join(cmd_strs) + '\n')

    # Make processes
    processes = []
    for cmd_str, cmd in zip(cmd_strs, cmds):
        p_prev = processes[-1][1] if processes else None
        p_curr = Popen(cmd, env=env, stdout=PIPE, stdin=p_prev.stdout if p_prev else None)
        processes.append((cmd_str, p_curr))

    p_last = processes[-1][1]

    with open(path, 'w') as f:
        # Write data into file
        while True:
            data = p_last.stdout.read(512 * 1024)
            if len(data) == 0:
                break
            f.write(data)

        # Close processes
        for cmd_str, p in processes:
            p.stdout.close()
            if p.wait() != 0:
                raise BackupError('Command `{cmd_str}` returned non-zero exit status `{returncode}`'.format(
                    cmd_str=cmd_str,
                    returncode=p.returncode,
                ))


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

        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        # Loop through databases
        for db_name, db_config in settings.DATABASES.items():
            print '========== Backing up \'{0}\'...'.format(db_name)

            engine = db_config['ENGINE']
            engine_options = ENGINE_OPTIONS.get(engine)

            if not engine_options:
                print 'Backup for {0} engine not implemented.'.format(engine)
                print '========== ...skipped.\n'
                continue

            backup_base_name = '{db_name}-{backup_name}.{backup_extension}.gz'.format(
                db_name=db_name,
                backup_name=backup_name,
                backup_extension=engine_options['backup_extension'],
            )
            backup_file = os.path.join(BACKUP_DIR, backup_base_name)

            # Find and run backup command
            backup_func = engine_options['backup_func']

            backup_kwargs = {'backup_file': backup_file, 'db_config': db_config}
            if backup_func is do_postgresql_backup:
                backup_kwargs['pg_dump_options'] = options['pg_dump_options']

            try:
                backup_func(**backup_kwargs)
                print '========== ...done!\n'
            except BackupError as e:
                print e.message
                print '========== ...skipped.\n'
