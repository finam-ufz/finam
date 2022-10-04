"""
Unit tests for the adapters.base module.
"""

import unittest
from datetime import datetime, timedelta

import numpy as np

from finam.adapters.base import (
    Callback,
    GridCellCallback,
    GridToValue,
    Scale,
    ValueToGrid,
)
from finam.data.grid import Grid, GridSpec
from finam.modules.generators import CallbackGenerator


class TestCallback(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, {})},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = Callback(callback=lambda v, t: v * 2)

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

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
            callbacks={"Step": (lambda t: t.day - 1, {})},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = Scale(scale=2.0)

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.source.connect()
        self.source.validate()

    def test_callback_adapter(self):
        t = datetime(2000, 1, 1)
        self.assertEqual(self.adapter.get_data(t), 0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(t), 2)
        self.source.update()
        self.assertEqual(self.adapter.get_data(t), 4)


class TestGridCallback(unittest.TestCase):
    def setUp(self):
        grid = Grid(GridSpec(20, 10))
        grid.fill(1.0)
        for r in range(10):
            grid.set_masked(4, r)

        self.source = CallbackGenerator(
            callbacks={"Grid": (lambda t: grid, {})},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = GridCellCallback(callback=lambda x, y, v, t: v + (t.day - 1) + x)

        self.source.initialize()

        self.source.outputs["Grid"] >> self.adapter

        self.source.connect()
        self.source.validate()

    def test_grid_callback_adapter(self):
        t = datetime(2000, 1, 1)

        self.assertEqual(self.adapter.get_data(t).get(0, 0), 1.0)
        self.assertEqual(self.adapter.get_data(t).get(1, 0), 2.0)
        self.assertEqual(self.adapter.get_data(t).get(2, 0), 3.0)

        self.assertTrue(self.adapter.get_data(t).get(4, 0) is np.ma.masked)

        self.source.update()

        t = datetime(2000, 1, 2)

        self.assertEqual(self.adapter.get_data(t).get(0, 0), 2.0)
        self.assertEqual(self.adapter.get_data(t).get(1, 0), 3.0)
        self.assertEqual(self.adapter.get_data(t).get(2, 0), 4.0)


class TestGridToValue(unittest.TestCase):
    def setUp(self):
        grid = Grid(GridSpec(20, 10))
        grid.fill(1.0)

        self.source = CallbackGenerator(
            callbacks={"Grid": (lambda t: grid, {})},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.source.initialize()

    def test_grid_to_value_mean(self):
        self.adapter = GridToValue(func=np.ma.mean)
        self.source.outputs["Grid"] >> self.adapter

        self.source.connect()
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1))
        self.assertEqual(result, 1.0)

    def test_grid_to_value_sum(self):
        self.adapter = GridToValue(func=np.ma.sum)
        self.source.outputs["Grid"] >> self.adapter

        self.source.connect()
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1))
        self.assertEqual(result, 200.0)


class TestValueToGrid(unittest.TestCase):
    def setUp(self):
        matrix = Grid(GridSpec(10, 10))
        matrix.fill(1.0)

        self.source = CallbackGenerator(
            callbacks={"Value": (lambda t: 1.0, {})},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.source.initialize()

    def test_value_to_grid(self):
        self.adapter = ValueToGrid(GridSpec(10, 10))
        self.source.outputs["Value"] >> self.adapter

        self.source.connect()
        self.source.validate()

        reference = Grid(GridSpec(10, 10))
        reference.fill(1.0)

        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1)), reference)


if __name__ == "__main__":
    unittest.main()
