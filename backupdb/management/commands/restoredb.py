from __future__ import absolute_import
from optparse import make_option
from subprocess import CalledProcessError
import logging
import os

from django.core.management.base import CommandError
from django.conf import settings
from django.db import close_connection

from backupdb.utils import get_latest_timestamped_file
from backupdb.settings import get_backup_directory, BACKUP_CONFIG
from backupdb.utils import BaseBackupDbCommand

logger = logging.getLogger(__name__)


class Command(BaseBackupDbCommand):
    help = 'Restores each database in settings.DATABASES from latest db backup.'

    option_list = BaseBackupDbCommand.option_list + (
        make_option(
            '--backup-name',
            help=(
                'Name of backup to restore from.  Example: '
                '`--backup-name=mybackup` will restore any backups that look '
                'like "default-mybackup.pgsql.gz".  Defaults to latest '
                'timestamped backup name.'
            ),
        ),
        make_option(
            '--drop-tables',
            action='store_true',
            default=False,
            help=(
                '** USE WITH CAUTION ** Drop all tables in databases before '
                'restoring them. The SQL dumps which are created by backupdb '
                'have drop statements so, usually, this option is not '
                'necessary.'
            ),
        ),
        make_option(
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
        ),
    )

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)

        # Django is querying django_content_types in a hanging transaction
        # Because of this psql can't drop django_content_types and just hangs
        close_connection()

        backup_directory = get_backup_directory()

        # Ensure backup dir present
        if not os.path.exists(backup_directory):
            raise CommandError("Backup dir {!r} does not exist!".format(
                backup_directory))

        backup_name = options['backup_name']
        drop_tables = options['drop_tables']
        show_output = options['show_output']

        # Loop through databases
        for db_name, db_config in settings.DATABASES.items():
            logger.info("Restoring {!r}".format(db_name))
            engine = db_config['ENGINE']
            try:
                backup_cls = BACKUP_CONFIG[engine]
            except KeyError:
                logger.error(
                    "Restore for {!r} engine not implemented".format(engine))
                continue  # TODO: Raise an error by default
                          # TODO: implement --ignore-errors



            if backup_name:
                fname = '{db}-{suffix}.{ext}.gz'.format(
                    db=db_name,
                    suffix=backup_suffix,
                    ext=backup_cls.extension,
                )
            else:
                fname = get_latest_timestamped_file(
                    db_name, backup_cls.extension, backup_directory)
                if fname is None:
                    logger.error(
                        "Couldn't find a default backup for '{!r}'".format(
                            db_name)
                    )
                    continue  # TODO: Raise an error by default
                              # TODO: implement --ignore-errors

            absolute_fname = os.path.join(backup_directory, fname)

            backup = backup_cls(
                db_config=db_config,
                backup_file=absolute_fname,
                show_output=show_output,
            )

            backup.do_restore(drop_tables=drop_tables)
            logger.info("Restored {db_name!r} from {backup_file!r}".format(
                db_name=db_name,
                backup_file=absolute_fname))
