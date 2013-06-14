import unittest

from backupdb_utils.commands import (
    get_mysql_args,
    get_postgresql_args,
    get_postgresql_env,
    #do_mysql_backup,
    #do_postgres_backup,
    #do_sqlite_backup,
    do_mysql_restore,
    do_postgresql_restore,
    do_sqlite_restore,
)
from backupdb_utils.exceptions import RestoreError


DB_CONFIG = {
    'NAME': 'test_db',
    'USER': 'test_user',
    'PASSWORD': 'test_password',
    'HOST': 'test_host',
    'PORT': 12345,
}


def make_db_config(*keys):
    new_dict = {}
    for k in keys:
        new_dict[k] = DB_CONFIG[k]
    return new_dict


class RequireBackupExistsTestCase(unittest.TestCase):
    def test_it_raises_an_exception_when_the_path_in_backup_file_arg_doesnt_exist(self):
        self.assertRaises(RestoreError, do_mysql_restore, backup_file='i_dont_exist', db_config={})
        self.assertRaises(RestoreError, do_postgresql_restore, backup_file='i_dont_exist', db_config={})
        self.assertRaises(RestoreError, do_sqlite_restore, backup_file='i_dont_exist', db_config={})


class GetMysqlArgsTestCase(unittest.TestCase):
    def test_it_builds_the_correct_args(self):
        self.assertEqual(
            get_mysql_args(make_db_config(
                'NAME',
                'USER',
            )),
            [
                '--user=test_user',
                'test_db',
            ],
        )
        self.assertEqual(
            get_mysql_args(make_db_config(
                'NAME',
                'USER',
                'PASSWORD',
            )),
            [
                '--user=test_user',
                '--password=test_password',
                'test_db',
            ],
        )
        self.assertEqual(
            get_mysql_args(make_db_config(
                'NAME',
                'USER',
                'PASSWORD',
                'HOST',
            )),
            [
                '--user=test_user',
                '--password=test_password',
                '--host=test_host',
                'test_db',
            ],
        )
        self.assertEqual(
            get_mysql_args(make_db_config(
                'NAME',
                'USER',
                'PASSWORD',
                'HOST',
                'PORT',
            )),
            [
                '--user=test_user',
                '--password=test_password',
                '--host=test_host',
                '--port=12345',
                'test_db',
            ],
        )


class GetPostgresqlArgsTestCase(unittest.TestCase):
    def test_it_builds_the_correct_args(self):
        self.assertEqual(
            get_postgresql_args(make_db_config(
                'NAME',
                'USER',
            )),
            [
                '--username=test_user',
                'test_db',
            ],
        )
        self.assertEqual(
            get_postgresql_args(make_db_config(
                'NAME',
                'USER',
                'HOST',
            )),
            [
                '--username=test_user',
                '--host=test_host',
                'test_db',
            ],
        )
        self.assertEqual(
            get_postgresql_args(make_db_config(
                'NAME',
                'USER',
                'HOST',
                'PORT',
            )),
            [
                '--username=test_user',
                '--host=test_host',
                '--port=12345',
                'test_db',
            ],
        )

    def test_it_correctly_includes_extra_args(self):
        self.assertEqual(
            get_postgresql_args(
                make_db_config(
                    'NAME',
                    'USER',
                ),
                extra_args='--no-owner --no-privileges',
            ),
            [
                '--username=test_user',
                '--no-owner',
                '--no-privileges',
                'test_db',
            ],
        )


class GetPostgresqlEnvTestCase(unittest.TestCase):
    def test_it_builds_the_correct_env_dict(self):
        self.assertTrue(
            get_postgresql_env(make_db_config('USER', 'NAME')) is None,
        )
        self.assertEqual(
            get_postgresql_env(make_db_config('USER', 'NAME', 'PASSWORD')),
            {'PGPASSWORD': 'test_password'},
        )
