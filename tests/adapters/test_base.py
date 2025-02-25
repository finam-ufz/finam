"""
Unit tests for the adapters.base module.
"""

import unittest
from datetime import datetime, timedelta

import numpy as np
from numpy.testing import assert_allclose

import finam as fm
from finam import UNITS, Info, NoGrid, UniformGrid
from finam import data as fmdata
from finam.adapters.base import Callback, GridToValue, Scale, ValueToGrid
from finam.components.generators import CallbackGenerator


class TestCallback(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)

        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=start,
            step=timedelta(1.0),
        )

        self.adapter = Callback(callback=lambda v, t: v * 2)

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid()))
        self.source.connect(start)
        self.source.connect(start)
        self.source.validate()

    def test_callback_adapter(self):
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1), None), 0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2), None), 2)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 3), None), 4)


class TestScale(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=start,
            step=timedelta(1.0),
        )

        self.adapter = Scale(scale=2.0)

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid()))
        self.source.connect(start)
        self.source.connect(start)
        self.source.validate()

    def test_callback_adapter(self):
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1), None), 0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2), None), 2)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 3), None), 4)


class TestGridToValue(unittest.TestCase):
    def setUp(self):
        grid, data = create_grid(20, 10, 1.0)

        self.source = CallbackGenerator(
            callbacks={"Grid": (lambda t: data, Info(None, grid=grid, units="m"))},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.source.initialize()

    def test_grid_to_value_mean(self):
        self.adapter = GridToValue(func=np.ma.mean)
        self.source.outputs["Grid"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid(), units=None))
        self.source.connect(datetime(2000, 1, 1))
        self.source.connect(datetime(2000, 1, 1))
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1), None)
        self.assertEqual(result, 1.0 * UNITS.meter)

    def test_grid_to_value_sum(self):
        self.adapter = GridToValue(func=np.ma.sum)
        self.source.outputs["Grid"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid(), units=None))
        self.source.connect(datetime(2000, 1, 1))
        self.source.connect(datetime(2000, 1, 1))
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1), None)
        self.assertEqual(result, 200.0 * UNITS.meter)


class TestValueToGrid(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: 1.0,
                    Info(None, grid=NoGrid(), units="m"),
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

        self.adapter.get_info(Info(None, grid=grid, units=None))
        self.source.connect(datetime(2000, 1, 1))
        self.source.connect(datetime(2000, 1, 1))
        self.source.validate()

        _reference_grid, reference_data = create_grid(10, 10, 1.0)
        out_data = self.adapter.get_data(datetime(2000, 1, 1), None)

        assert_allclose(fmdata.get_magnitude(out_data)[0, ...], reference_data)
        self.assertEqual(fmdata.get_units(out_data), UNITS("m"))

    def test_value_to_grid_wrong_grid(self):
        grid, data = create_grid(10, 10, 1.0)

        self.adapter = ValueToGrid(grid)
        self.source.outputs["Value"] >> self.adapter

        with self.assertRaises(fm.FinamMetaDataError):
            self.adapter.get_info(Info(None, grid=UniformGrid((2, 2)), units=None))

    def test_value_to_grid_from_target(self):
        grid, data = create_grid(10, 10, 1.0)

        self.adapter = ValueToGrid(None)
        self.source.outputs["Value"] >> self.adapter

        self.adapter.get_info(Info(None, grid=grid, units=None))
        self.source.connect(datetime(2000, 1, 1))
        self.source.connect(datetime(2000, 1, 1))
        self.source.validate()

        _reference_grid, reference_data = create_grid(10, 10, 1.0)
        out_data = self.adapter.get_data(datetime(2000, 1, 1), None)

        assert_allclose(fmdata.get_magnitude(out_data)[0, ...], reference_data)
        self.assertEqual(fmdata.get_units(out_data), UNITS("m"))


def create_grid(cols, rows, value):
    grid = UniformGrid((cols, rows), data_location="POINTS")

    data = np.full(shape=grid.data_shape, fill_value=value, order=grid.order)

    return grid, data


if __name__ == "__main__":
    unittest.main()
