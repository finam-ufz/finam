"""
Unit tests for the adapters.base module.
"""

import unittest
from datetime import datetime, timedelta

import numpy as np
import pint
import pint_xarray
import xarray as xr
from numpy.testing import assert_allclose

from finam.adapters.base import Callback, GridToValue, Scale, ValueToGrid
from finam.data import Info, NoGrid, UniformGrid
from finam.modules.generators import CallbackGenerator

reg = pint.UnitRegistry(force_ndarray_like=True)


class TestCallback(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info())},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = Callback(callback=lambda v, t: v * 2)

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(grid=NoGrid))
        self.source.connect()
        self.source.validate()

    def test_callback_adapter(self):
        t = datetime(2000, 1, 1)
        self.assertEqual(self.adapter.get_data(t), 0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(t), 2)
        self.source.update()
        self.assertEqual(self.adapter.get_data(t), 4)


class TestScale(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info())},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = Scale(scale=2.0)

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(grid=NoGrid))
        self.source.connect()
        self.source.validate()

    def test_callback_adapter(self):
        t = datetime(2000, 1, 1)
        self.assertEqual(self.adapter.get_data(t), 0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(t), 2)
        self.source.update()
        self.assertEqual(self.adapter.get_data(t), 4)


class TestGridToValue(unittest.TestCase):
    def setUp(self):
        grid, data = create_grid(20, 10, 1.0)

        self.source = CallbackGenerator(
            callbacks={"Grid": (lambda t: data, Info(grid=grid))},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.source.initialize()

    def test_grid_to_value_mean(self):
        self.adapter = GridToValue(func=np.ma.mean)
        self.source.outputs["Grid"] >> self.adapter

        self.adapter.get_info(Info(grid=NoGrid))
        self.source.connect()
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1))
        self.assertEqual(result, xr.DataArray(1.0).pint.quantify(reg.meter))

    def test_grid_to_value_sum(self):
        self.adapter = GridToValue(func=np.ma.sum)
        self.source.outputs["Grid"] >> self.adapter

        self.adapter.get_info(Info(grid=NoGrid))
        self.source.connect()
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1))
        self.assertEqual(result, xr.DataArray(200.0).pint.quantify(reg.meter))


class TestValueToGrid(unittest.TestCase):
    def setUp(self):

        self.source = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: xr.DataArray(1.0).pint.quantify(reg.meter),
                    Info(grid=NoGrid),
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.source.initialize()

    def test_value_to_grid(self):
        grid, data = create_grid(10, 10, 1.0)

        self.adapter = ValueToGrid(grid)
        self.source.outputs["Value"] >> self.adapter

        self.adapter.get_info(Info(grid=NoGrid))
        self.source.connect()
        self.source.validate()

        _reference_grid, reference_data = create_grid(10, 10, 1.0)
        out_data = self.adapter.get_data(datetime(2000, 1, 1))

        assert_allclose(out_data.pint.magnitude, reference_data.pint.magnitude)
        self.assertEqual(out_data.pint.units, reference_data.pint.units)


def create_grid(cols, rows, value):
    grid = UniformGrid((cols, rows), data_location="POINTS")

    data = xr.DataArray(
        np.full(shape=grid.data_shape, fill_value=value, order=grid.order)
    ).pint.quantify(reg.meter)

    return grid, data


if __name__ == "__main__":
    unittest.main()
