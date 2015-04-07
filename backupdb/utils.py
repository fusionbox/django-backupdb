import os
import glob
import re
import logging

from django.core.management.base import BaseCommand

TIMESTAMP_PATTERNS = (
    r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}',  # New ISO format pattern
    r'\d{4}-\d{2}-\d{2}-\d{10}',  # Old style pattern
)


def get_latest_timestamped_file(name, ext, directory):
    """
    Gets the latest timestamped backup file name with the given database type
    extension.
    """
    for pat in TIMESTAMP_PATTERNS:
        matcher = re.compile(r'^{}-{}\.{}'.format(
            re.escape(name), pat, re.escape(ext)))

        files = [f for f in os.listdir(directory) if matcher.match(f)]
        files.sort(reverse=True)

        try:
            return files[0]
        except IndexError:
            continue

    return None


def apply_arg_values(*args):
    """
    Apply argument to values::

        >>> apply_arg_values(('--name={}', 'name'),
        ...                  ('--password={}', 'password'),
        ...                  ('--level={}', ''),
        ...                  ('--last={}', None))
        ['--name=name', '--password=password']

    """
    return [a.format(v) for a, v in args if v]


# TODO: Get rid of BaseBackupDbCommand
class BaseBackupDbCommand(BaseCommand):
    can_import_settings = True

    LOG_LEVELS = {
        0: logging.ERROR,
        1: logging.INFO,
        2: logging.DEBUG,
        3: logging.DEBUG,
    }
    LOG_FORMAT = '%(asctime)s - %(levelname)-8s: %(message)s'

    def _setup_logging(self, level):
        level = int(level)
        logging.basicConfig(format=self.LOG_FORMAT, level=self.LOG_LEVELS[level])

    def handle(self, *args, **options):
        self._setup_logging(options['verbosity'])
