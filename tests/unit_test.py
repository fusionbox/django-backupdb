import tempfile
import shutil
import os
import unittest

from backupdb.utils import get_latest_timestamped_file


class GetLatestFileTest(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.mkdtemp(suffix='backupdb')


    def tearDown(self):
        shutil.rmtree(self.directory)

    def create_files(self, file_list):
        for fname in file_list:
            absolute_fname = os.path.join(self.directory, fname)
            open(absolute_fname, 'w').close()

    def test_can_find_old_format(self):
        self.create_files([
            'default-2013-05-02-1367553089.sqlite.gz',
            'default-2013-06-06-1370570260.sqlite.gz',
            'default-2013-06-06-1370580510.sqlite.gz',

            'default-2013-05-02-1367553089.mysql.gz',
            'default-2013-06-06-1370570260.mysql.gz',
            'default-2013-06-06-1370580510.mysql.gz',

            'default-2013-05-02-1367553089.pgsql.gz',
            'default-2013-06-06-1370570260.pgsql.gz',
            'default-2013-06-06-1370580510.pgsql.gz',
        ])

        sqlite = get_latest_timestamped_file(
            'default', 'sqlite', directory=self.directory)
        assert sqlite == 'default-2013-06-06-1370580510.sqlite.gz'


        mysql = get_latest_timestamped_file(
            'default', 'mysql', directory=self.directory)
        assert mysql == 'default-2013-06-06-1370580510.mysql.gz'

        postgresql = get_latest_timestamped_file(
            'default', 'pgsql', directory=self.directory)
        assert postgresql == 'default-2013-06-06-1370580510.pgsql.gz'

    def test_can_find_new_format(self):
        self.create_files([
            'default-2015-04-06T00:00:00.000000.sqlite.gz',
            'default-2015-04-06T00:01:00.000000.sqlite.gz',
            'default-2015-04-06T01:00:00.000000.sqlite.gz',
        ])

        fname = get_latest_timestamped_file(
            'default', 'sqlite', directory=self.directory)

        assert fname == 'default-2015-04-06T01:00:00.000000.sqlite.gz'


        self.create_files([
            'default-2015-04-07T00:00:00.000000.sqlite.gz',
            'default-2015-05-06T00:00:00.000000.sqlite.gz',
            'default-2016-04-06T00:00:00.000000.sqlite.gz',
        ])

        fname = get_latest_timestamped_file(
            'default', 'sqlite', directory=self.directory)

        assert fname == 'default-2016-04-06T00:00:00.000000.sqlite.gz'

    def test_cant_find_file(self):
        default = get_latest_timestamped_file(
            '', '', directory=self.directory)
        assert default is None

        mysql = get_latest_timestamped_file(
            'default', 'mysql', directory=self.directory)
        assert mysql is None
