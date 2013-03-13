#!/usr/bin/env python

from os.path import dirname, abspath
import os
import sys

from django.conf import settings


if not settings.configured and not os.environ.get('DJANGO_SETTINGS_MODULE'):
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'backupdb_database',
                'TEST_NAME': 'test_backupdb_database',
            },
            'mysql': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'backupdb',
                'USER': 'root',
            },
            'postgresql': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'backupdb',
                'USER': 'backupdb_user',
            },
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',

            'backupdb',
            'tests',
        ],
        ROOT_URLCONF='',
        DEBUG=False,
        SITE_ID=1,
    )


from django.test.simple import DjangoTestSuiteRunner


def runtests():
    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)

    test_runner = DjangoTestSuiteRunner(verbosity=1, interactive=False, failfast=False)
    failures = test_runner.run_tests(['tests'])

    sys.exit(failures)


if __name__ == '__main__':
    runtests()
