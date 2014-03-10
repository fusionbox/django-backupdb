from backupdb.utils.exceptions import RestoreError
from backupdb.utils.files import get_latest_timestamped_file

from backupdb.tests.utils import FileSystemScratchTestCase


class GetLatestTimestampedFileTestCase(FileSystemScratchTestCase):
    def create_files(self, *args):
        for file in args:
            open(self.get_path(file), 'a').close()

    def test_it_returns_the_latest_timestamped_file_with_ext(self):
        self.create_files(
            'default-2013-05-02-1367553089.sqlite.gz',
            'default-2013-06-06-1370570260.sqlite.gz',
            'default-2013-06-06-1370580510.sqlite.gz',

            'default-2013-05-02-1367553089.mysql.gz',
            'default-2013-06-06-1370570260.mysql.gz',
            'default-2013-06-06-1370580510.mysql.gz',

            'default-2013-05-02-1367553089.pgsql.gz',
            'default-2013-06-06-1370570260.pgsql.gz',
            'default-2013-06-06-1370580510.pgsql.gz',
        )

        sqlite_file = get_latest_timestamped_file('sqlite', dir=self.SCRATCH_DIR)
        mysql_file = get_latest_timestamped_file('mysql', dir=self.SCRATCH_DIR)
        pgsql_file = get_latest_timestamped_file('pgsql', dir=self.SCRATCH_DIR)

        self.assertEqual(sqlite_file, self.get_path('default-2013-06-06-1370580510.sqlite.gz'))
        self.assertEqual(mysql_file, self.get_path('default-2013-06-06-1370580510.mysql.gz'))
        self.assertEqual(pgsql_file, self.get_path('default-2013-06-06-1370580510.pgsql.gz'))

    def test_it_raises_an_exception_when_no_files_found(self):
        self.assertRaises(RestoreError, get_latest_timestamped_file, '', dir=self.SCRATCH_DIR)
        self.assertRaises(RestoreError, get_latest_timestamped_file, 'mysql', dir=self.SCRATCH_DIR)
