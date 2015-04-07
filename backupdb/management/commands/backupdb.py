from __future__ import absolute_import
from optparse import make_option
from subprocess import CalledProcessError
import logging
import os
from datetime import datetime

from django.conf import settings
from django.utils import timezone

from backupdb.utils import BaseBackupDbCommand
from backupdb.settings import get_backup_directory, BACKUP_CONFIG

logger = logging.getLogger(__name__)


class Command(BaseBackupDbCommand):
    help = 'Backs up each database in settings.DATABASES.'

    option_list = BaseBackupDbCommand.option_list + (
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
        super(Command, self).handle(*args, **options)

        current_time_string = timezone.now().isoformat()

        backup_suffix = options['backup_name']
        if backup_suffix is None:
            backup_suffix = current_time_string

        show_output = options['show_output']

        backup_directory = get_backup_directory()

        # Ensure backup dir present
        if not os.path.exists(backup_directory):
            os.makedirs(backup_directory)

        # Loop through databases
        for db_name, db_config in settings.DATABASES.items():
            logger.info("Starting to backup {!r}".format(db_name))
            engine = db_config['ENGINE']
            try:
                backup_cls = BACKUP_CONFIG[engine]
            except KeyError:
                logger.error(
                    "Backup for {!r} engine not implemented".format(engine))
                continue  # TODO: Raise an error by default
                          # TODO: implement --ignore-errors

            fname = '{db}-{suffix}.{ext}.gz'.format(
                db=db_name,
                suffix=backup_suffix,
                ext=backup_cls.extension,
            )
            absolute_fname = os.path.join(backup_directory, fname)

            backup = backup_cls(
                db_config=db_config,
                backup_file=absolute_fname,
                show_output=show_output,
            )


            try:
                backup.do_backup()
            except RuntimeError as e:
                logger.error(e.message)
            else:
                logger.info(
                    "Backup of {db_name!r} saved in {backup_file!r}".format(
                        db_name=db_name,
                        backup_file=fname
                    )
                )
