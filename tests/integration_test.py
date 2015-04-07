import tempfile
import shutil

import dj_database_url
db_config = dj_database_url.config()

from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': db_config},
    INSTALLED_APPS=('django.contrib.contenttypes', 'backupdb', )
)

from django.db import models
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.core import management
from django.contrib.contenttypes.models import ContentType
import django

if hasattr(django, 'setup'):  # Django > 1.6
    django.setup()  # Setup the app registry


class BackupTest(SimpleTestCase):

    def setUp(self):
        self.backup_dir = tempfile.mkdtemp('backupdb')
        self._settings = override_settings(BACKUPDB_DIRECTORY=self.backup_dir)
        self._settings.enable()

    def test_backupdb(self):
        management.call_command('syncdb')

        ct = ContentType.objects.create()
        # There should be a default content
        assert ContentType.objects.filter(pk=ct.pk).exists()

        management.call_command('backupdb')

        ContentType.objects.all().delete()
        assert not ContentType.objects.filter(pk=ct.pk).exists()

        management.call_command('restoredb')

        assert ContentType.objects.filter(pk=ct.pk).exists()

    def tearDown(self):
        self._settings.disable()
        shutil.rmtree(self.backup_dir)
