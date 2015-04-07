from __future__ import absolute_import
import os

import spm

from backupdb.utils import apply_arg_values
from backupdb.backends.base import BaseBackend

# TODO: Use this command to drop tables from a database
PG_DROP_SQL = """SELECT format('DROP TABLE IF EXISTS %I CASCADE;', tablename)
                 FROM pg_tables WHERE schemaname = 'public';"""


class PostgreSQLBackend(BaseBackend):
    extension = 'pgsql'

    def get_env(self):
        try:
            return {'PGPASSWORD': self.db_config['PASSWORD']}
        except KeyError:
            return {}

    def get_arguments(self):
        return apply_arg_values(
            ('--username={0}', self.db_config.get('USER')),
            ('--host={0}', self.db_config.get('HOST')),
            ('--port={0}', self.db_config.get('PORT')),
        )

    def get_backup_command(self):
        arguments = ['pg_dump', '--clean'] + self.get_arguments() + \
                        self.extra_args + [database]
        env = self.get_env()
        return spm.run(*arguments, env=env)

    def get_restore_command(self, drop_tables):
        # TODO: Drop all tables from the database if drop_tables is True
        database = self.db_config['NAME']

        if not os.path.isfile(self.backup_file):
            raise RuntimeError("{} does not exist".format(fname))

        arguments = ['psql'] + self.get_arguments() + self.extra_args + \
                        [database]
        env = self.get_env()

        return spm.run(*arguments, env=env)
