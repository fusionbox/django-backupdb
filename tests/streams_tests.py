from mock import patch, call
import sys
import unittest

from backupdb_utils.streams import out, err, bar, set_verbosity, SectionError, section


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


class OutTestCase(PatchStandardStreamsTestCase):
    def test_calling_out_writes_to_sys_stdout(self):
        out('Richard Dean Anderson is...', newline=False)
        out('MacGyver')

        self.assertStdOutCallsEqual(
            call('Richard Dean Anderson is...'),
            call('MacGyver\n'),
        )


class BarTestCase(PatchStandardStreamsTestCase):
    def test_calling_bar_writes_a_bar_to_the_given_stream(self):
        bar('Long ago, in a galaxy far away...', width=70, stream=sys.stderr)
        bar('test', width=10, stream=sys.stderr)

        self.assertStdErrCallsEqual(
            call('================== Long ago, in a galaxy far away... =================\n'),
            call('== test ==\n'),
        )

        bar('test', width=10, stream=sys.stdout)

        self.assertStdOutCallsEqual(
            call('== test ==\n'),
        )

    def test_calling_bar_writes_to_stderr_by_default(self):
        bar('test', width=10)

        self.assertStdErrCallsEqual(
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


class SetVerbosityTestCase(PatchStandardStreamsTestCase):
    def test_messages_higher_than_current_verbosity_level_are_ignored(self):
        set_verbosity(0)
        err('Shh...', verbosity=1)
        out('Shh...', verbosity=1)

        self.assertStdErrCallsEqual()

    def test_messages_lower_than_or_equal_to_current_verbosity_level_are_printed(self):
        set_verbosity(0)
        err('Shh...', verbosity=1)
        set_verbosity(1)
        err('...be vewy vewy kwiet...', verbosity=1)
        err("...I'm hunting wabbit...", verbosity=2)
        set_verbosity(2)
        out('FWEEZE WABBIT!', verbosity=2)

        self.assertStdErrCallsEqual(
            call('...be vewy vewy kwiet...\n'),
        )

        self.assertStdOutCallsEqual(
            call('FWEEZE WABBIT!\n'),
        )


class SectionTestCase(PatchStandardStreamsTestCase):
    def test_beginning_and_ending_bars_surround_code_executed_in_a_section_context(self):
        with section('Long ago, in a galaxy far away...'):
            err('Luke...I am your fathaa...')
            err('NOOO!!!')

        self.assertStdErrCallsEqual(
            call('//================ Long ago, in a galaxy far away... ===============\\\\\n'),
            call('Luke...I am your fathaa...\n'),
            call('NOOO!!!\n'),
            call('\\\\============================ ...done! ============================//\n'),
        )

    def test_raising_a_section_error_in_a_section_context_changes_the_ending_bar_caption(self):
        with section('Long ago, in a galaxy far away...'):
            raise SectionError('Mesa called Jar-Jar Binks. Mesa your humble servant.')

        self.assertStdErrCallsEqual(
            call('//================ Long ago, in a galaxy far away... ===============\\\\\n'),
            call('Mesa called Jar-Jar Binks. Mesa your humble servant.\n'),
            call('\\\\=========================== ...skipped. ==========================//\n'),
        )
