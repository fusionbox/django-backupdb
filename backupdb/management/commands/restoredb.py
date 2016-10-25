from __future__ import absolute_import
from optparse import make_option
from subprocess import CalledProcessError
import logging
import os

from django.core.management.base import CommandError
from django.conf import settings

from backupdb.utils.commands import BaseBackupDbCommand
from backupdb.utils.exceptions import RestoreError
from backupdb.utils.files import get_latest_timestamped_file
from backupdb.utils.log import section, SectionError, SectionWarning
from backupdb.utils.settings import BACKUP_DIR, BACKUP_CONFIG

logger = logging.getLogger(__name__)


class Command(BaseBackupDbCommand):
    help = 'Restores each database in settings.DATABASES from latest db backup.'

    def add_arguments(self, parser):

        parser.add_argument(
            '--backup-name',
            help=(
                'Name of backup to restore from.  Example: '
                '`--backup-name=mybackup` will restore any backups that look '
                'like "default-mybackup.pgsql.gz".  Defaults to latest '
                'timestamped backup name.'
            ),
        )
        parser.add_argument(
            '--drop-tables',
            action='store_true',
            default=False,
            help=(
                '** USE WITH CAUTION ** Drop all tables in databases before '
                'restoring them. The SQL dumps which are created by backupdb '
                'have drop statements so, usually, this option is not '
                'necessary.'
            ),
        )
        parser.add_argument(
            '--show-output',
            action='store_true',
            default=False,
            help=(
                'Display the output of stderr and stdout (apart from data which '
                'is piped from one process to another) for processes that are '
                'run while restoring databases.  These are command-line '
                'programs such as `psql` or `mysql`.  This can be useful for '
                'understanding how restoration is failing in the case that it '
                'is.'
            ),
        )

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)

        # Ensure backup dir present
        if not os.path.exists(BACKUP_DIR):
            raise CommandError("Backup dir '{0}' does not exist!".format(BACKUP_DIR))

        backup_name = options['backup_name']
        drop_tables = options['drop_tables']
        show_output = options['show_output']

        # Loop through databases
        for db_name, db_config in settings.DATABASES.items():
            with section("Restoring '{0}'...".format(db_name)):
                # Get backup config for this engine type
                engine = db_config['ENGINE']
                backup_config = BACKUP_CONFIG.get(engine)
                if not backup_config:
                    raise SectionWarning("Restore for '{0}' engine not implemented".format(engine))

                # Get backup file name
                backup_extension = backup_config['backup_extension']
                if backup_name:
                    backup_file = '{dir}/{db_name}-{backup_name}.{ext}.gz'.format(
                        dir=BACKUP_DIR,
                        db_name=db_name,
                        backup_name=backup_name,
                        ext=backup_extension,
                    )
                else:
                    try:
                        backup_file = get_latest_timestamped_file(backup_extension)
                    except RestoreError as e:
                        raise SectionError(e)

                # Find restore command and get kwargs
                restore_func = backup_config['restore_func']
                restore_kwargs = {
                    'backup_file': backup_file,
                    'db_config': db_config,
                    'drop_tables': drop_tables,
                    'show_output': show_output,
                }

                # Run restore command
                try:
                    restore_func(**restore_kwargs)
                    logger.info("Restored '{db_name}' from '{backup_file}'".format(
                        db_name=db_name,
                        backup_file=backup_file))
                except (RestoreError, CalledProcessError) as e:
                    raise SectionError(e)
