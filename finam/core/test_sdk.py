"""
Unit tests for the sdk implementations.
"""

import unittest

from .sdk import AAdapter


class DummyAdapter(AAdapter):
    def __init__(self):
        super().__init__()

    def get_data(self, time):
        return time


class TestChaining(unittest.TestCase):
    def test_chaining(self):
        adapter1 = DummyAdapter()
        adapter2 = DummyAdapter()
        adapter3 = DummyAdapter()

        adapter1 >> adapter2 >> adapter3

        self.assertEqual(adapter1.targets, [adapter2])
        self.assertEqual(adapter2.targets, [adapter3])

        self.assertEqual(adapter2.source, adapter1)
        self.assertEqual(adapter3.source, adapter2)


if __name__ == "__main__":
    unittest.main()
