#!/usr/bin/env python

from setuptools import setup, find_packages


VERSION = '0.5.3'


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name='django-backupdb',
    version=VERSION,
    description='Management commands for backing up and restoring databases in Django.',
    long_description=readme(),
    author='Fusionbox programmers',
    author_email='programmers@fusionbox.com',
    keywords='django database backup',
    url='https://github.com/fusionbox/django-backupdb',
    packages=find_packages(exclude=('unit_tests', 'unit_tests_scratch')),
    platforms='any',
    license='Fusionbox',
    test_suite='nose.collector',
    setup_requires=[
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
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
)
