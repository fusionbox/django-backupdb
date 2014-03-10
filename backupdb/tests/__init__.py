import unittest

from . import commands
from . import files
from . import log
from . import processes


loader = unittest.TestLoader()

commands_tests = loader.loadTestsFromModule(commands)
files_tests = loader.loadTestsFromModule(files)
log_tests = loader.loadTestsFromModule(log)
processes_tests = loader.loadTestsFromModule(processes)

all_tests = unittest.TestSuite([
    commands_tests,
    files_tests,
    log_tests,
    processes_tests,
])
