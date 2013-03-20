#!/usr/bin/env python

from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


version = '0.4.1'


setup(name='django-backupdb',
      version=version,
      description='Management commands for backing up and restoring databases in Django.',
      long_description=readme(),
      author='Fusionbox programmers',
      author_email='programmers@fusionbox.com',
      keywords='django database backup',
      url='https://github.com/fusionbox/django-backupdb',
      packages=find_packages(exclude=('tests',)),
      platforms='any',
      license='BSD',
      test_suite='runtests.runtests',
      tests_require=[
          'django>=1.3',
          'mysql-python>=1.2.3',
          'psycopg2>=2.4.6',
      ],
      install_requires=[
          'django>=1.3',
      ],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Django',
      ])
