import os
import unittest
from pathlib import Path

from finam.tools.cwd_helper import execute_in_cwd


class Test:
    def __init__(self, cwd=None):
        self.cwd = cwd
        self.new_cwd = None

    @execute_in_cwd
    def change_cwd(self):
        self.new_cwd = os.getcwd()


class TestCWD(unittest.TestCase):
    def test_cwd(self):
        # no cwd set
        test1 = Test()
        with self.assertRaises(ValueError):
            test1.change_cwd()
        # assert we were in the right cwd
        test2 = Test("..")
        test2.change_cwd()
        self.assertEqual(Path(test2.cwd).resolve(), Path(test2.new_cwd).resolve())
