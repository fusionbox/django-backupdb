#!/usr/bin/env python
import subprocess
import sys
import os

from setuptools import setup


version = (0, 6, 0, 'alpha')

current_path = os.path.dirname(__file__)

sys.path.append(current_path)


def get_version():
    number = '.'.join(map(str, version[:3]))
    stage = version[3]
    if stage == 'final':
        return number
    elif stage == 'alpha':
        process = subprocess.Popen('git rev-parse HEAD'.split(), stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return number + '-' + stdout.decode('utf-8').strip()[:8]


def get_readme():
    with open(os.path.join(current_path, 'README.rst'), 'r') as f:
        return f.read()

# TODO: Integrate py.test in python setup.py test

setup(
    name='django-backupdb',
    version=get_version(),
    description='Management commands for backing up and restoring databases in Django.',
    long_description=get_readme(),
    author='Fusionbox programmers',
    author_email='programmers@fusionbox.com',
    keywords='django database backup',
    url='https://github.com/fusionbox/django-backupdb',
    packages=['backupdb', 'backupdb.backends', 'backupdb.management',
              'backupdb.management.commands'],
    platforms='any',
    license='BSD',
    tests_require=[
        'dj_database_url==0.3.0',
    ],
    install_requires=[
        'Django>=1.4',
        'spm',  # This avoid implementing subcommands in backupdb
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License'
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
