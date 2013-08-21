from optparse import make_option
from subprocess import CalledProcessError
import os
import time

from django.core.management.base import BaseCommand

from backupdb_utils.commands import do_postgresql_backup
from backupdb_utils.exceptions import BackupError
from backupdb_utils.settings import BACKUP_DIR, BACKUP_CONFIG
from backupdb_utils.streams import err, section, SectionError, set_verbosity


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
        make_option(
            '--show-output',
            action='store_true',
            default=False,
            help=(
                'Display the output of stderr and stdout (apart from data which '
                'is piped from one process to another) for processes that are '
                'run while backing up databases.  These are command-line '
                'programs such as `psql` or `mysql`.  This can be useful for '
                'understanding how backups are failing in the case that they '
                'are.'
            ),
        ),
    )

    def handle(self, *args, **options):
        from django.conf import settings

        current_time = time.strftime('%F-%s')
        backup_name = options['backup_name'] or current_time
        show_output = options['show_output']

        set_verbosity(int(options['verbosity']))

        # Ensure backup dir present
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        # Loop through databases
        for db_name, db_config in settings.DATABASES.items():
            with section("Backing up '{0}'...".format(db_name)):
                # Get backup config for this engine type
                engine = db_config['ENGINE']
                backup_config = BACKUP_CONFIG.get(engine)
                if not backup_config:
                    raise SectionError("! Backup for '{0}' engine not implemented".format(engine))

                # Get backup file name
                backup_base_name = '{db_name}-{backup_name}.{backup_extension}.gz'.format(
                    db_name=db_name,
                    backup_name=backup_name,
                    backup_extension=backup_config['backup_extension'],
                )
                backup_file = os.path.join(BACKUP_DIR, backup_base_name)

                # Find backup command and get kwargs
                backup_func = backup_config['backup_func']
                backup_kwargs = {
                    'backup_file': backup_file,
                    'db_config': db_config,
                    'show_output': show_output,
                }
                if backup_func is do_postgresql_backup:
                    backup_kwargs['pg_dump_options'] = options['pg_dump_options']

                # Run backup command
                try:
                    backup_func(**backup_kwargs)
                    err("* Backup of '{db_name}' saved in '{backup_file}'".format(
                        db_name=db_name,
                        backup_file=backup_file))
                except (BackupError, CalledProcessError) as e:
                    raise SectionError('! {0}'.format(e))
