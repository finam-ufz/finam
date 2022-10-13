import unittest
from datetime import datetime as dt

import numpy as np

import finam


class TestDataTools(unittest.TestCase):
    def test_check(self):
        grid = finam.data.EsriGrid(2, 3)
        gri0 = finam.data.EsriGrid(2, 3, axes_names=["lat", "lon"])
        gri1 = finam.data.EsriGrid(3, 2)

        info = finam.data.Info(grid, units="m", foo="bar")
        inf0 = info.copy_with(units="meter")
        inf1 = info.copy_with(foo="spam")
        inf2 = info.copy_with(units="s")
        inf3 = info.copy_with(grid=gri0)
        inf4 = info.copy_with(grid=gri1)

        time = dt(year=2022, month=10, day=12)
        tim0 = dt(year=2021, month=10, day=12)

        data = np.arange(6).reshape(3, 2)
        dar0 = finam.data.tools.to_xarray(data, "data", info, time)
        dar1 = finam.data.tools.to_xarray(data, "data", info)

        # should work
        finam.data.tools.check(dar0, "data", info, time)
        finam.data.tools.check(dar1, "data", info)

        # no DataArray
        with self.assertRaises(finam.data.tools.FinamDataError):
            finam.data.tools.check(None, "data", info, time)

        # not qunatified
        with self.assertRaises(finam.data.tools.FinamDataError):
            finam.data.tools.check(dar0.pint.dequantify(), "data", info, time)

        # wrong name
        with self.assertRaises(finam.data.tools.FinamDataError):
            finam.data.tools.check(dar0, "wrong", info, time)

        # wrong time
        with self.assertRaises(finam.data.tools.FinamDataError):
            finam.data.tools.check(dar0, "data", info, tim0)

        # no time to check
        with self.assertRaises(finam.data.tools.FinamDataError):
            finam.data.tools.check(dar0, "data", info)

        # no time in xdata
        with self.assertRaises(finam.data.tools.FinamDataError):
            finam.data.tools.check(dar1, "data", info, time)

        # should work for no-time data
        finam.data.tools.check(dar1, "data", inf0)

        # other units format should work
        finam.data.tools.check(dar0, "data", inf0, time)

        # wrong meta
        with self.assertRaises(finam.data.tools.FinamDataError):
            finam.data.tools.check(dar0, "data", inf1, time)

        # wrong units
        with self.assertRaises(finam.data.tools.FinamDataError):
            finam.data.tools.check(dar0, "data", inf2, time)

        # wrong dims
        with self.assertRaises(finam.data.tools.FinamDataError):
            finam.data.tools.check(dar0, "data", inf3, time)

        # wrong shape
        with self.assertRaises(finam.data.tools.FinamDataError):
            finam.data.tools.check(dar0, "data", inf4, time)
        with self.assertRaises(finam.data.tools.FinamDataError):
            finam.data.tools.check(dar1, "data", inf4)
