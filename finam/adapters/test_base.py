import unittest

import numpy as np

from modules.generators import CallbackGenerator
from data.grid import Grid, GridSpec

from .base import Callback, PerCellCallback, GridToValue, ValueToGrid


class TestCallback(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(callbacks={"Step": lambda t: t}, step=1)
        self.adapter = Callback(callback=lambda v, t: v * 2)

        self.source.initialize()

        self.source.outputs()["Step"] >> self.adapter

        self.source.connect()
        self.source.validate()

    def test_callback_adapter(self):
        self.assertEqual(self.adapter.get_data(0), 0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(0), 2)
        self.source.update()
        self.assertEqual(self.adapter.get_data(0), 4)


class TestGridCallback(unittest.TestCase):
    def setUp(self):
        grid = Grid(GridSpec(20, 10))
        grid.fill(1.0)

        self.source = CallbackGenerator(callbacks={"Grid": lambda t: grid}, step=1)
        self.adapter = PerCellCallback(callback=lambda x, y, v, t: v + t + x)

        self.source.initialize()

        self.source.outputs()["Grid"] >> self.adapter

        self.source.connect()
        self.source.validate()

    def test_grid_callback_adapter(self):
        self.assertEqual(self.adapter.get_data(0).get(0, 0), 1.0)
        self.assertEqual(self.adapter.get_data(0).get(1, 0), 2.0)
        self.assertEqual(self.adapter.get_data(0).get(2, 0), 3.0)

        self.source.update()

        self.assertEqual(self.adapter.get_data(1).get(0, 0), 2.0)
        self.assertEqual(self.adapter.get_data(1).get(1, 0), 3.0)
        self.assertEqual(self.adapter.get_data(1).get(2, 0), 4.0)


class TestGridToValue(unittest.TestCase):
    def setUp(self):
        grid = Grid(GridSpec(20, 10))
        grid.fill(1.0)

        self.source = CallbackGenerator(callbacks={"Grid": lambda t: grid}, step=1)

        self.source.initialize()

    def test_grid_to_value_mean(self):
        self.adapter = GridToValue(func=np.mean)
        self.source.outputs()["Grid"] >> self.adapter

        self.source.connect()
        self.source.validate()

        self.assertEqual(self.adapter.get_data(0), 1.0)

    def test_grid_to_value_sum(self):
        self.adapter = GridToValue(func=np.sum)
        self.source.outputs()["Grid"] >> self.adapter

        self.source.connect()
        self.source.validate()

        self.assertEqual(self.adapter.get_data(0), 200.0)


class TestValueToGrid(unittest.TestCase):
    def setUp(self):
        matrix = Grid(GridSpec(10, 10))
        matrix.fill(1.0)

        self.source = CallbackGenerator(callbacks={"Value": lambda t: 1.0}, step=1)

        self.source.initialize()

    def test_value_to_grid(self):
        self.adapter = ValueToGrid(GridSpec(10, 10))
        self.source.outputs()["Value"] >> self.adapter

        self.source.connect()
        self.source.validate()

        reference = Grid(GridSpec(10, 10))
        reference.fill(1.0)

        self.assertEqual(self.adapter.get_data(0), reference)


if __name__ == "__main__":
    unittest.main()
