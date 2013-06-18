from django import db
from django.core.management import call_command
from django.utils import unittest

from backupdb.tests.models import TestModel


class BackupDBRestoreDBCommandsTestCase(unittest.TestCase):
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

        db.close_connection()

        call_command('restoredb')

        self.assertEqual(
            list(self.sqlite.values_list('id', 'name')),
            [
                (1, u'TestSqlite1'),
                (2, u'TestSqlite2'),
                (3, u'TestSqlite3'),
            ],
        )
        self.assertEqual(
            list(self.mysql.values_list('id', 'name')),
            [
                (1, u'TestMysql1'),
                (2, u'TestMysql2'),
            ],
        )
        self.assertEqual(
            list(self.postgresql.values_list('id', 'name')),
            [
                (1, u'TestPostgresql1'),
            ],
        )
