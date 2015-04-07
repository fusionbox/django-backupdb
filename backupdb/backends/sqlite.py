from __future__ import absolute_import

import spm

from backupdb.backends.base import BaseBackend


class SQLite3Backend(BaseBackend):
    extension = 'sqlite'

    def get_backup_command(self, fname):
        arguments = ['sqlite3'] + self.extra_args + [fname, '.dump']
        command = spm.run(*arguments)

        return command

    def get_restore_command(self, fname, drop_tables):
        # TODO: Drop all tables from the database if drop_tables is True
        return spm.run('sqlite3', fname)
