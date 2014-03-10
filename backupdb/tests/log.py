import unittest

from backupdb.utils.log import bar


class BarTestCase(unittest.TestCase):
    def test_it_should_return_a_string_with_text_centered_in_a_bar(self):
        self.assertEqual(
            bar('test', width=70),
            '================================ test ================================',
        )

    def test_it_should_return_a_bar_string_with_the_specified_width(self):
        test_bar1 = r'=========================== test ==========================='
        test_bar2 = r'//========================= test =========================\\'
        test_bar3 = r'\\========================= test =========================//'

        self.assertEqual(len(test_bar1), 60)
        self.assertEqual(len(test_bar2), 60)
        self.assertEqual(len(test_bar3), 60)

        self.assertEqual(bar('test', width=60), test_bar1)
        self.assertEqual(bar('test', width=60, position='top'), test_bar2)
        self.assertEqual(bar('test', width=60, position='bottom'), test_bar3)

    def test_it_should_work_even_if_the_given_width_is_less_than_the_message_length(self):
        self.assertEqual(bar('test', width=0), '== test ==')
        self.assertEqual(bar('test', width=0, position='top'), r'// test \\')
        self.assertEqual(bar('test', width=0, position='bottom'), r'\\ test //')

    def test_it_should_render_a_top_bottom_or_plain_bar_depending_on_the_position_argument(self):
        test_bar1 = r'================================ test ================================'
        test_bar2 = r'//============================== test ==============================\\'
        test_bar3 = r'\\============================== test ==============================//'

        self.assertEqual(bar('test', width=70), test_bar1)
        self.assertEqual(bar('test', width=70, position='top'), test_bar2)
        self.assertEqual(bar('test', width=70, position='bottom'), test_bar3)

    def test_it_should_allow_the_message_to_be_blank(self):
        test_bar1 = r'======================================================================'
        test_bar2 = r'//==================================================================\\'
        test_bar3 = r'\\==================================================================//'

        self.assertEqual(bar(width=70), test_bar1)
        self.assertEqual(bar(width=70, position='top'), test_bar2)
        self.assertEqual(bar(width=70, position='bottom'), test_bar3)
