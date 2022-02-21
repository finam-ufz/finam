"""
Unit tests for the adapters.probe module.
"""

import unittest
from datetime import datetime

from finam.core.sdk import Input, Output
from finam.adapters.probe import CallbackProbe


class TestProbe(unittest.TestCase):
    def test_probe_adapter(self):
        data = None
        time = None

        def callback(d, t):
            nonlocal data
            nonlocal time
            data = d
            time = t

        out = Output()
        adapter = CallbackProbe(callback=callback)
        inp = Input()

        out >> adapter >> inp

        out.push_data(100, datetime(2000, 1, 1))
        inp.pull_data(datetime(2000, 1, 1))

        self.assertEqual(data, 100)
        self.assertEqual(time, datetime(2000, 1, 1))


if __name__ == "__main__":
    unittest.main()
