"""
Unit tests for the adapters.probe module.
"""

import unittest

from core.sdk import Input, Output
from ..probe import CallbackProbe


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

        out.push_data(100, 0)
        inp.pull_data(0)

        self.assertEqual(data, 100)
        self.assertEqual(time, 0)


if __name__ == "__main__":
    unittest.main()
