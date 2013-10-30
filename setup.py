#!/usr/bin/env python

from setuptools import setup, find_packages
import subprocess


version = (0, 5, 4, 'final')


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
    with open('README.rst') as f:
        return f.read()


setup(
    name='django-backupdb',
    version=get_version(),
    description='Management commands for backing up and restoring databases in Django.',
    long_description=get_readme(),
    author='Fusionbox programmers',
    author_email='programmers@fusionbox.com',
    keywords='django database backup',
    url='https://github.com/fusionbox/django-backupdb',
    packages=find_packages(exclude=('unit_tests', 'unit_tests_scratch')),
    platforms='any',
    license='Fusionbox',
    test_suite='nose.collector',
    setup_requires=[
        'nose>=1.2.1',
    ],
    tests_require=[
        'nose>=1.2.1',
        'mock>=1.0.1',
        'coverage>=3.6',
    ],
    install_requires=[
        'django>=1.3',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
)
