#!/usr/bin/env python

# http://ericholscher.com/blog/2009/jun/29/enable-setuppy-test-your-django-apps/
# http://www.travisswicegood.com/2010/01/17/django-virtualenv-pip-and-fabric/
# http://code.djangoproject.com/svn/django/trunk/tests/runtests.py
import os
import sys

# fix sys path so we don't need to setup PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'backupdb.tests.settings'

import django
from django.conf import settings
from django.test.utils import get_runner


def usage():
    return """
Usage: python runend2end.py [UnitTestCase].[method]

You can pass the class name of a specific test case you want to run.  You may
also run a particular test in a test case by specifying its method name.
"""


def main():
    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    if len(sys.argv) == 2:
        test_case = '.' + sys.argv[1]
    elif len(sys.argv) == 1:
        test_case = ''
    else:
        print(usage())
        sys.exit(1)

    test_module_name = 'backupdb.tests'
    if django.VERSION[0] == 1 and django.VERSION[1] < 6:
        test_module_name = 'tests'

    failures = test_runner.run_tests([test_module_name + test_case])

    sys.exit(failures)


if __name__ == '__main__':
    main()
