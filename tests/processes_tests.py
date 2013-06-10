import os
import unittest

from backupdb_utils.processes import extend_env


class ExtendEnvTestCase(unittest.TestCase):
    def test_extend_env_creates_a_copy_of_the_current_env(self):
        env = extend_env({'arst': 1234})
        self.assertFalse(env is os.environ)

    #def test_extend_env_adds_keys_to_a_copy_of_the_current_env(self):
        #self.assertNotEqual(
        #env = extend_env({'arst': 1234})
        #self.assertFalse(env is os.environ)
