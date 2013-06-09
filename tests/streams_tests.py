from mock import patch, call
import unittest

from backupdb_utils.streams import err, bar, set_verbosity, SectionError, section


class PatchStandardStreamsTestCase(unittest.TestCase):
    def setUp(self):
        self.stdout_patcher = patch('sys.stdout')
        self.stderr_patcher = patch('sys.stderr')
        self.mock_stdout = self.stdout_patcher.start()
        self.mock_stderr = self.stderr_patcher.start()

    def tearDown(self):
        self.stdout_patcher.stop()
        self.stderr_patcher.stop()

    def assertStdOutCallsEqual(self, *args):
        self.assertEqual(self.mock_stdout.write.call_args_list, list(args))

    def assertStdErrCallsEqual(self, *args):
        self.assertEqual(self.mock_stderr.write.call_args_list, list(args))


class ErrTestCase(PatchStandardStreamsTestCase):
    def test_calling_err_writes_to_sys_stderr(self):
        err('Richard Dean Anderson is...', newline=False)
        err('MacGyver')

        self.assertStdErrCallsEqual(
            call('Richard Dean Anderson is...'),
            call('MacGyver\n'),
        )


class BarTestCase(PatchStandardStreamsTestCase):
    def test_calling_bar_writes_a_bar_to_the_given_stream(self):
        bar('Long ago, in a galaxy far away...', width=70)
        bar('test', width=10)

        self.assertStdErrCallsEqual(
            call('================== Long ago, in a galaxy far away... =================\n'),
            call('== test ==\n'),
        )

    def test_bars_default_to_width_70(self):
        bar('Long ago, in a galaxy far away...')

        self.assertStdErrCallsEqual(
            call('================== Long ago, in a galaxy far away... =================\n'),
        )

    def test_calling_bar_without_message_prints_full_bar(self):
        bar(width=10)

        self.assertStdErrCallsEqual(
            call('==========\n'),
        )

    def test_calling_bar_with_the_position_argument_prints_beginning_and_ending_bars(self):
        bar('Richard Dean Anderson is...', position='top', width=50)
        bar('...MacGyver', position='bottom', width=50)

        self.assertStdErrCallsEqual(
            call('//========= Richard Dean Anderson is... ========\\\\\n'),
            call('\\\\================= ...MacGyver ================//\n'),
        )

    def test_calling_bar_with_explicit_stream(self):
        import sys
        bar('test', width=10, stream=sys.stdout)

        self.assertStdOutCallsEqual(
            call('== test ==\n'),
        )
