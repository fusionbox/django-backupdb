#!/usr/bin/env python

from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='django-backupdb',
      version='1.0',
      description='Management commands for backing up and restoring databases in Django.',
      long_description=readme(),
      author='Fusionbox programmers',
      author_email='programmers@fusionbox.com',
      keywords='django database backup',
      url='https://github.com/fusionbox/django-backupdb',
      packages=find_packages(),
      platforms="any",
      license='BSD',
      classifiers=[
          'Environment :: Web Environment',
          'Framework :: Django',
      ])
