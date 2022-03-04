"""
Unit tests for the adapters.time module.
"""

import unittest
from datetime import datetime, timedelta

from finam.adapters.time import (
    LinearIntegration,
    LinearInterpolation,
    NextValue,
    PreviousValue,
)
from finam.data.grid import Grid, GridSpec
from finam.modules.generators import CallbackGenerator


class TestNextValue(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": lambda t: t.day - 1},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = NextValue()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.source.connect()
        self.source.validate()

    def test_next_value(self):
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0)), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 12)), 1.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 0)), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 12)), 2.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 3, 0)), 2.0)


class TestPreviousValue(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": lambda t: t.day - 1},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = PreviousValue()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.source.connect()
        self.source.validate()

    def test_previous_value(self):
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0)), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 12)), 0.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 0)), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 12)), 1.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 3, 0)), 2.0)


class TestLinearInterpolation(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": lambda t: t.day - 1},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = LinearInterpolation()

        self.source.initialize()
        self.source.outputs["Step"] >> self.adapter

        self.source.connect()
        self.source.validate()

    def test_linear_interpolation(self):
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0)), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 12)), 0.5)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 0)), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 12)), 1.5)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 3, 0)), 2.0)


class TestLinearGridInterpolation(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Grid": lambda t: create_grid(t.day - 1)},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = LinearInterpolation()

        self.source.initialize()
        self.source.outputs["Grid"] >> self.adapter

        self.source.connect()
        self.source.validate()

    def test_linear_grid_interpolation(self):
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0)).get(2, 3), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 12)).get(2, 3), 0.5)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 0)).get(2, 3), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 12)).get(2, 3), 1.5)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 3, 0)).get(2, 3), 2.0)


class TestLinearIntegration(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": lambda t: t.day - 1},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = LinearIntegration()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.source.connect()
        self.source.validate()

    def test_linear_integration(self):
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 12)), 0.25)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 0)), 0.75)
        self.source.update()
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 4, 0)), 2.0)


class TestLinearGridIntegration(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Grid": lambda t: create_grid(t.day - 1)},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = LinearIntegration()

        self.source.initialize()

        self.source.outputs["Grid"] >> self.adapter

        self.source.connect()
        self.source.validate()

    def test_linear_grid_integration(self):
        self.source.update()
        self.assertEqual(
            self.adapter.get_data(datetime(2000, 1, 1, 12)).get(2, 3), 0.25
        )
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 0)).get(2, 3), 0.75)
        self.source.update()
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 4, 0)).get(2, 3), 2.0)


def create_grid(t):
    grid = Grid(GridSpec(10, 5))
    grid.fill(t)

    for r in range(5):
        grid.set_masked(4, r)

    return grid


if __name__ == "__main__":
    unittest.main()
