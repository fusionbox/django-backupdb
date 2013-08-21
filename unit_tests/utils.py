import os
import unittest


class FileSystemScratchTestCase(unittest.TestCase):
    SCRATCH_DIR = 'unit_tests_scratch'

    @classmethod
    def get_path(cls, file):
        return os.path.join(cls.SCRATCH_DIR, file)

    @classmethod
    def clear_scratch_dir(cls):
        """
        Deletes all scratch files in the tests scratch directory.
        """
        for file in os.listdir(cls.SCRATCH_DIR):
            if file != '.gitkeep':
                os.remove(cls.get_path(file))

    def setUp(self):
        self.clear_scratch_dir()

    def tearDown(self):
        self.clear_scratch_dir()

    def assertFileExists(self, file):
        self.assertTrue(os.path.exists(self.get_path(file)))

    def assertFileHasLength(self, file, length):
        with open(self.get_path(file)) as f:
            content = f.read()
            self.assertEqual(len(content), length)

    def assertFileHasContent(self, file, expected_content):
        with open(self.get_path(file)) as f:
            actual_content = f.read()
            self.assertEqual(actual_content, expected_content)

    def assertInFile(self, file, expected_content):
        with open(self.get_path(file)) as f:
            actual_content = f.read()
            self.assertTrue(expected_content in actual_content)
