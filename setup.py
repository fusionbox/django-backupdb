#!/usr/bin/env python

from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='django-backupdb',
      version='0.2',
      description='Management commands for backing up and restoring databases in Django.',
      long_description=readme(),
      author='David Sanders',
      author_email='davesque@gmail.com',
      keywords='django database backup',
      url='https://github.com/davesque/django-backupdb',
      packages=find_packages(),
      platforms='any',
      license='MIT',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Django',
      ])
