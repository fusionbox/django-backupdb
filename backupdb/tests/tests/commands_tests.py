from django.core.management import call_command
from django.utils import unittest

from .models import TestModel


class BackupDBCommandTestCase(unittest.TestCase):
    multi_db = True

    def setUp(self):
        self.sqlite = TestModel.objects.using('default')
        self.mysql = TestModel.objects.using('mysql')
        self.postgresql = TestModel.objects.using('postgresql')

    def make_test_records(self):
        """
        Creates some test records.  Fixtures don't seem to work.
        """
        self.sqlite.create(name='TestSqlite1')
        self.sqlite.create(name='TestSqlite2')
        self.sqlite.create(name='TestSqlite3')

        self.mysql.create(name='TestMysql1')
        self.mysql.create(name='TestMysql2')

        self.postgresql.create(name='TestPostgresql1')

    def test_can_backup(self):
        self.make_test_records()

        self.assertEqual(self.sqlite.count(), 3)
        self.assertEqual(self.mysql.count(), 2)
        self.assertEqual(self.postgresql.count(), 1)

        call_command('backupdb')

        self.sqlite.all().delete()
        self.mysql.all().delete()
        self.postgresql.all().delete()

        self.assertEqual(self.sqlite.count(), 0)
        self.assertEqual(self.mysql.count(), 0)
        self.assertEqual(self.postgresql.count(), 0)

    def test_can_restore_from_backup(self):
        self.assertEqual(self.sqlite.count(), 0)
        self.assertEqual(self.mysql.count(), 0)
        self.assertEqual(self.postgresql.count(), 0)

        call_command('restoredb')

        self.assertEqual(self.sqlite.count(), 3)
        self.assertEqual(self.mysql.count(), 2)
        self.assertEqual(self.postgresql.count(), 1)
