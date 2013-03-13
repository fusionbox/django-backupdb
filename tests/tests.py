from django.core.management import call_command
from django.test import TestCase

from backupdb.management.commands.backupdb import Command as BackupDBCommand
from backupdb.management.commands.restoredb import Command as RestoreDBCommand


class BackupDBCommandTestCase(TestCase):
    def test_assert(self):
        call_command('backupdb')
        self.assertTrue(True)
