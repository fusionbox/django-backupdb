from subprocess import CalledProcessError
import os
import unittest

try:
    from collections import OrderedDict
except ImportError:
    # This should only happen in Python 2.6
    # SortedDict is deprecated in Django 1.7 and will be removed in Django 1.9
    from django.utils.datastructures import SortedDict as OrderedDict

from backupdb.utils.processes import (
    extend_env,
    get_env_str,
    pipe_commands,
    pipe_commands_to_file,
)

from .utils import FileSystemScratchTestCase


class ExtendEnvTestCase(unittest.TestCase):
    def test_extend_env_creates_a_copy_of_the_current_env(self):
        env = extend_env({'BACKUPDB_TEST_ENV_SETTING': 1234})
        self.assertFalse(env is os.environ)

    def test_extend_env_adds_keys_to_a_copy_of_the_current_env(self):
        env = extend_env({
            'BACKUPDB_TEST_ENV_SETTING_1': 1234,
            'BACKUPDB_TEST_ENV_SETTING_2': 1234,
        })

        orig_keys = set(os.environ.keys())
        curr_keys = set(env.keys())
        diff_keys = curr_keys - orig_keys

        self.assertEqual(diff_keys, set([
            'BACKUPDB_TEST_ENV_SETTING_1',
            'BACKUPDB_TEST_ENV_SETTING_2',
        ]))


class GetEnvStrTestCase(unittest.TestCase):
    def test_get_env_str_works_for_empty_dicts(self):
        self.assertEqual(get_env_str({}), '')

    def test_get_env_str_works_for_non_empty_dicts(self):
        self.assertEqual(
            get_env_str({'VAR_1': 1234}),
            "VAR_1='1234'",
        )
        self.assertEqual(
            get_env_str(OrderedDict([
                ('VAR_1', 1234),
                ('VAR_2', 'arst'),
            ])),
            "VAR_1='1234' VAR_2='arst'",
        )
        self.assertEqual(
            get_env_str(OrderedDict([
                ('VAR_1', 1234),
                ('VAR_2', 'arst'),
                ('VAR_3', 'zxcv'),
            ])),
            "VAR_1='1234' VAR_2='arst' VAR_3='zxcv'",
        )


class PipeCommandsTestCase(FileSystemScratchTestCase):
    def test_it_pipes_a_list_of_commands_into_each_other(self):
        pipe_commands([
            ['echo', r"""
import sys
for i in range(4):
    sys.stdout.write('spam\n')
"""],
            ['python'],
            ['tee', self.get_path('pipe_commands.out')],
        ])

        self.assertFileExists('pipe_commands.out')
        self.assertFileHasContent(
            'pipe_commands.out',
            'spam\nspam\nspam\nspam\n',
        )

    def test_it_works_when_large_amounts_of_data_are_being_piped(self):
        pipe_commands([
            ['echo', r"""
import sys
for i in range(400000):
    sys.stdout.write('spam\n')
"""],
            ['python'],
            ['tee', self.get_path('pipe_commands.out')],
        ])

        self.assertFileExists('pipe_commands.out')
        self.assertFileHasLength('pipe_commands.out', 2000000)
        self.assertInFile('pipe_commands.out', 'spam\nspam\nspam\n')

    def test_it_allows_you_to_specify_extra_environment_variables(self):
        pipe_commands([
            ['echo', """
import os
import sys
sys.stdout.write(os.environ['TEST_VAR'])
"""],
            ['python'],
            ['tee', self.get_path('pipe_commands.out')],
        ], extra_env={'TEST_VAR': 'spam'})

        self.assertFileExists('pipe_commands.out')
        self.assertFileHasContent('pipe_commands.out', 'spam')

    def test_it_correctly_raises_a_called_process_error_when_necessary(self):
        self.assertRaises(CalledProcessError, pipe_commands, [['false'], ['true']])


class PipeCommandsToFileTestCase(FileSystemScratchTestCase):
    def test_it_pipes_a_list_of_commands_into_each_other_and_then_into_a_file(self):
        pipe_commands_to_file([
            ['echo', r"""
import sys
for i in range(4):
    sys.stdout.write('spam\n')
"""],
            ['python'],
        ], self.get_path('pipe_commands.out'))

        self.assertFileExists('pipe_commands.out')
        self.assertFileHasContent(
            'pipe_commands.out',
            'spam\nspam\nspam\nspam\n',
        )

    def test_it_works_when_large_amounts_of_data_are_being_piped(self):
        pipe_commands_to_file([
            ['echo', r"""
import sys
for i in range(400000):
    sys.stdout.write('spam\n')
"""],
            ['python'],
        ], self.get_path('pipe_commands.out'))

        self.assertFileExists('pipe_commands.out')
        self.assertFileHasLength('pipe_commands.out', 2000000)
        self.assertInFile('pipe_commands.out', 'spam\nspam\nspam\n')

    def test_it_allows_you_to_specify_extra_environment_variables(self):
        pipe_commands_to_file([
            ['echo', """
import os
import sys
sys.stdout.write(os.environ['TEST_VAR'])
"""],
            ['python'],
        ], self.get_path('pipe_commands.out'), extra_env={'TEST_VAR': 'spam'})

        self.assertFileExists('pipe_commands.out')
        self.assertFileHasContent('pipe_commands.out', 'spam')

    def test_it_correctly_raises_a_called_process_error_when_necessary(self):
        self.assertRaises(
            CalledProcessError,
            pipe_commands_to_file,
            [['false'], ['true']],
            self.get_path('pipe_commands.out'),
        )
