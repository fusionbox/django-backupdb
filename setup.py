#!/usr/bin/env python
import sys
import os

from setuptools import setup

version = '0.7.0'

current_path = os.path.dirname(__file__)

sys.path.append(current_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')


def get_readme():
    with open(os.path.join(current_path, 'README.rst'), 'r') as f:
        return f.read()

setup(
    name='django-backupdb',
    version=version,
    description='Management commands for backing up and restoring databases in Django.',
    long_description=get_readme(),
    author='Fusionbox programmers',
    author_email='programmers@fusionbox.com',
    keywords='django database backup',
    url='https://github.com/fusionbox/django-backupdb',
    packages=['backupdb', 'backupdb.utils', 'backupdb.management',
              'backupdb.management.commands', 'backupdb.tests',
              'backupdb.tests.app'],
    platforms='any',
    license='Fusionbox',
    test_suite='backupdb.tests.all_tests',
    tests_require=[
        'mock>=1.0.1',
        'dj_database_url==0.3.0',
    ],
    install_requires=[
        'Django>=1.4',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
)
