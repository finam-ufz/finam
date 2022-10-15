"""
Unit tests for the adapters.probe module.
"""

import unittest
from datetime import datetime

from finam.adapters.probe import CallbackProbe
from finam.core.sdk import Input, Output
from finam.data import Info, NoGrid, tools


class TestProbe(unittest.TestCase):
    def test_probe_adapter(self):
        data = None
        time = None

        def callback(d, t):
            nonlocal data
            nonlocal time
            data = d
            time = t

        out = Output("test_out")
        adapter = CallbackProbe(callback=callback)
        inp = Input("test_in")

        out >> adapter >> inp

        out.push_info(Info(grid=NoGrid(), units="m"))
        inp.exchange_info(Info(grid=NoGrid(), units=None))
        out.push_data(100 * tools.UNITS.Unit("m"), datetime(2000, 1, 1))
        inp.pull_data(datetime(2000, 1, 1))

        self.assertEqual(data, 100 * tools.UNITS.Unit("m"))
        self.assertEqual(time, datetime(2000, 1, 1))


if __name__ == "__main__":
    unittest.main()
