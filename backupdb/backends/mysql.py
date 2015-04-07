from __future__ import absolute_import
import os

import spm

from backupdb.utils import apply_arg_values
from backupdb.backends.base import BaseBackend


class MySQLBackend(BaseBackend):
    extension = 'mysql'

    def get_arguments(self):
        return apply_arg_values(
            ('--user={}', self.db_config.get('USER')),
            ('--password={}', self.db_config.get('PASSWORD')),
            ('--host={}', self.db_config.get('HOST')),
            ('--port={}', self.db_config.get('PORT'))
        )

    def get_backup_command(self, db_name):
        arguments = ['mysqldump'] + self.get_arguments() + self.extra_args + \
                        [db_name]
        return spm.run(*arguments)

    def get_restore_command(self, db_name, drop_tables):
        # TODO: Drop all tables from the database if drop_tables is True

        arguments = ['mysql'] + self.get_arguments() + self.extra_args + \
                        [db_name]
        return spm.run(*arguments)
