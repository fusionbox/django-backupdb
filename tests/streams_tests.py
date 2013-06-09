from mock import patch, call
import unittest

from backupdb_utils.streams import err, bar, set_verbosity, SectionError, section


class PatchStdErrTestCase(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('sys.stderr')
        self.mock_stderr = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def assertCallsEqual(self, *args):
        self.assertEqual(self.mock_stderr.write.call_args_list, list(args))


class ErrTestCase(PatchStdErrTestCase):
    def test_calling_err_writes_to_sys_stderr(self):
        err('Richard Dean Anderson is...', newline=False)
        err('MacGyver')

        self.assertCallsEqual(
            call('Richard Dean Anderson is...'),
            call('MacGyver\n'),
        )


class BarTestCase(PatchStdErrTestCase):
    def test_calling_bar_writes_a_bar_to_the_given_stream(self):
        bar('Long ago, in a galaxy far away...', width=70)

        self.assertCallsEqual(
            call('================== Long ago, in a galaxy far away... =================\n'),
        )
