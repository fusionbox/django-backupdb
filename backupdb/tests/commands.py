from mock import call, patch
import unittest

from backupdb.utils.commands import (
    PG_DROP_SQL,
    get_mysql_args,
    get_postgresql_args,
    get_postgresql_env,
    do_mysql_backup,
    do_postgresql_backup,
    do_sqlite_backup,
    do_mysql_restore,
    do_postgresql_restore,
    do_sqlite_restore,
)
from backupdb.utils.exceptions import RestoreError


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


class MockOsPathExists(object):
    """
    Used as a mock object for os.path.exists.
    """
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return True


class PatchPipeCommandsTestCase(unittest.TestCase):
    """
    Used for testing of pipe_commands and pipe_commands_to_file.
    """
    def setUp(self):
        self.pipe_commands_patcher = patch('backupdb.utils.commands.pipe_commands')
        self.pipe_commands_to_file_patcher = patch('backupdb.utils.commands.pipe_commands_to_file')
        self.os_patcher = patch('os.path.exists', new_callable=MockOsPathExists)

        self.mock_pipe_commands = self.pipe_commands_patcher.start()
        self.mock_pipe_commands_to_file = self.pipe_commands_to_file_patcher.start()
        self.mock_os = self.os_patcher.start()

    def tearDown(self):
        self.pipe_commands_patcher.stop()
        self.pipe_commands_to_file_patcher.stop()
        self.os_patcher.stop()

    def assertPipeCommandsCallsEqual(self, *args):
        self.assertEqual(self.mock_pipe_commands.call_args_list, list(args))

    def assertPipeCommandsToFileCallsEqual(self, *args):
        self.assertEqual(self.mock_pipe_commands_to_file.call_args_list, list(args))


class RequireBackupExistsTestCase(unittest.TestCase):
    def test_it_raises_an_exception_when_the_path_in_backup_file_arg_doesnt_exist(self):
        self.assertRaises(RestoreError, do_mysql_restore, backup_file='i_dont_exist', db_config={})
        self.assertRaises(RestoreError, do_postgresql_restore, backup_file='i_dont_exist', db_config={})
        self.assertRaises(RestoreError, do_sqlite_restore, backup_file='i_dont_exist', db_config={})


class GetMysqlArgsTestCase(unittest.TestCase):
    def test_it_builds_the_correct_args(self):
        self.assertEqual(
            get_mysql_args(make_db_config('NAME', 'USER')),
            [
                '--user=test_user',
                'test_db',
            ],
        )
        self.assertEqual(
            get_mysql_args(make_db_config('NAME', 'USER', 'PASSWORD')),
            [
                '--user=test_user',
                '--password=test_password',
                'test_db',
            ],
        )
        self.assertEqual(
            get_mysql_args(make_db_config('NAME', 'USER', 'PASSWORD', 'HOST')),
            [
                '--user=test_user',
                '--password=test_password',
                '--host=test_host',
                'test_db',
            ],
        )
        self.assertEqual(
            get_mysql_args(make_db_config('NAME', 'USER', 'PASSWORD', 'HOST', 'PORT')),
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
            get_postgresql_args(make_db_config('NAME', 'USER')),
            [
                '--username=test_user',
                'test_db',
            ],
        )
        self.assertEqual(
            get_postgresql_args(make_db_config('NAME', 'USER', 'HOST')),
            [
                '--username=test_user',
                '--host=test_host',
                'test_db',
            ],
        )
        self.assertEqual(
            get_postgresql_args(make_db_config('NAME', 'USER', 'HOST', 'PORT')),
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
                make_db_config('NAME', 'USER'),
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


class DoMysqlBackupTestCase(PatchPipeCommandsTestCase):
    def test_it_makes_correct_calls_to_processes_api(self):
        do_mysql_backup('test.mysql.gz', DB_CONFIG)

        self.assertPipeCommandsToFileCallsEqual(call(
            [
                [
                    'mysqldump',
                    '--user=test_user',
                    '--password=test_password',
                    '--host=test_host',
                    '--port=12345',
                    'test_db',
                ],
                ['gzip'],
            ],
            path='test.mysql.gz',
            show_stderr=False,
        ))


class DoPostgresqlBackupTestCase(PatchPipeCommandsTestCase):
    def test_it_makes_correct_calls_to_processes_api(self):
        do_postgresql_backup('test.pgsql.gz', DB_CONFIG)

        self.assertPipeCommandsToFileCallsEqual(call(
            [
                [
                    'pg_dump',
                    '--clean',
                    '--username=test_user',
                    '--host=test_host',
                    '--port=12345',
                    'test_db',
                ],
                ['gzip'],
            ],
            path='test.pgsql.gz',
            extra_env={'PGPASSWORD': 'test_password'},
            show_stderr=False,
        ))


class DoSqliteBackupTestCase(PatchPipeCommandsTestCase):
    def test_it_makes_correct_calls_to_processes_api(self):
        do_sqlite_backup('test.sqlite.gz', DB_CONFIG)

        self.assertPipeCommandsToFileCallsEqual(call(
            [['cat', 'test_db'], ['gzip']],
            path='test.sqlite.gz',
            show_stderr=False,
        ))


class DoMysqlRestoreTestCase(PatchPipeCommandsTestCase):
    def test_it_makes_correct_calls_to_processes_api(self):
        do_mysql_restore(backup_file='test.mysql.gz', db_config=DB_CONFIG)

        self.assertPipeCommandsCallsEqual(call(
            [
                ['cat', 'test.mysql.gz'],
                ['gunzip'],
                [
                    'mysql',
                    '--user=test_user',
                    '--password=test_password',
                    '--host=test_host',
                    '--port=12345',
                    'test_db',
                ],
            ],
            show_stderr=False,
            show_last_stdout=False,
        ))

    def test_it_drops_tables_before_restoring_if_specified(self):
        do_mysql_restore(backup_file='test.mysql.gz', db_config=DB_CONFIG, drop_tables=True)

        self.assertPipeCommandsCallsEqual(
            call(
                [
                    [
                        'mysqldump',
                        '--user=test_user',
                        '--password=test_password',
                        '--host=test_host',
                        '--port=12345',
                        'test_db',
                        '--no-data',
                    ],
                    ['grep', '^DROP'],
                    [
                        'mysql',
                        '--user=test_user',
                        '--password=test_password',
                        '--host=test_host',
                        '--port=12345',
                        'test_db',
                    ],
                ],
                show_stderr=False,
                show_last_stdout=False,
            ),
            call(
                [
                    ['cat', 'test.mysql.gz'],
                    ['gunzip'],
                    [
                        'mysql',
                        '--user=test_user',
                        '--password=test_password',
                        '--host=test_host',
                        '--port=12345',
                        'test_db',
                    ],
                ],
                show_stderr=False,
                show_last_stdout=False,
            ),
        )


class DoPostgresqlRestoreTestCase(PatchPipeCommandsTestCase):
    def test_it_makes_correct_calls_to_processes_api(self):
        do_postgresql_restore(backup_file='test.pgsql.gz', db_config=DB_CONFIG)

        self.assertPipeCommandsCallsEqual(call(
            [
                ['cat', 'test.pgsql.gz'],
                ['gunzip'],
                [
                    'psql',
                    '--username=test_user',
                    '--host=test_host',
                    '--port=12345',
                    'test_db',
                ],
            ],
            extra_env={'PGPASSWORD': 'test_password'},
            show_stderr=False,
            show_last_stdout=False,
        ))

    def test_it_drops_tables_before_restoring_if_specified(self):
        do_postgresql_restore(backup_file='test.pgsql.gz', db_config=DB_CONFIG, drop_tables=True)

        self.assertPipeCommandsCallsEqual(
            call(
                [
                    [
                        'psql',
                        '--username=test_user',
                        '--host=test_host',
                        '--port=12345',
                        'test_db',
                        '-t',
                        '-c',
                        PG_DROP_SQL,
                    ],
                    [
                        'psql',
                        '--username=test_user',
                        '--host=test_host',
                        '--port=12345',
                        'test_db',
                    ],
                ],
                extra_env={'PGPASSWORD': 'test_password'},
                show_stderr=False,
                show_last_stdout=False,
            ),
            call(
                [
                    ['cat', 'test.pgsql.gz'],
                    ['gunzip'],
                    [
                        'psql',
                        '--username=test_user',
                        '--host=test_host',
                        '--port=12345',
                        'test_db',
                    ],
                ],
                extra_env={'PGPASSWORD': 'test_password'},
                show_stderr=False,
                show_last_stdout=False,
            ),
        )


class DoSqliteRestoreTestCase(PatchPipeCommandsTestCase):
    def test_it_makes_correct_calls_to_processes_api(self):
        do_sqlite_restore(backup_file='test.sqlite.gz', db_config=DB_CONFIG)

        self.assertPipeCommandsToFileCallsEqual(call(
            [['cat', 'test.sqlite.gz'], ['gunzip']],
            path='test_db',
            show_stderr=False,
        ))
