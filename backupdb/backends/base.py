# -*- coding: utf-8 -*-
import os
import abc

import spm
import six


class BaseBackend(six.with_metaclass(abc.ABCMeta, object)):
    def __init__(self, **kwargs):
        self.db_config = kwargs.pop('db_config')
        self.backup_file = kwargs.pop('backup_file')
        self.extra_args = kwargs.pop('extra_args', [])
        self.show_ouput = kwargs.pop('show_ouput', False)

    @abc.abstractmethod
    def get_backup_command(self, db_name):
        """
        Returns a spm command which dumps the database on stdout
        """

    @abc.abstractmethod
    def get_restore_command(self, db_name, drop_tables):
        """
        Returns a spm command which takes a backup file on stdin
        """

    def do_backup(self):
        db_name = self.db_config['NAME']  # This has to raise KeyError if it does
                                          # not exist.

        command = self.get_backup_command(db_name)

        proc = command.pipe('gzip')
        proc.stdout = open(self.backup_file, 'w')
        proc.wait()

    def do_restore(self, drop_tables):
        db_name = self.db_config['NAME']  # This has to raise KeyError if it does
                                          # not exist.

        if not os.path.isfile(self.backup_file):
            raise RuntimeError("{} does not exist".format(fname))

        command = self.get_restore_command(db_name, drop_tables=drop_tables)

        proc = spm.run('zcat', self.backup_file).pipe(command)
        proc.wait()
