"""
Unit tests for the adapters.time module.
"""
import unittest
from datetime import datetime, timedelta

import numpy as np
import pint

from finam.adapters.time import (
    LinearIntegration,
    LinearInterpolation,
    NextValue,
    PreviousValue,
)
from finam.core.interfaces import FinamTimeError
from finam.data import Info, NoGrid, UniformGrid, tools
from finam.modules.generators import CallbackGenerator

reg = pint.UnitRegistry(force_ndarray_like=True)


class TestNextValue(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(grid=NoGrid()))},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = NextValue()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(grid=NoGrid()))

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

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(datetime(2000, 1, 4, 0))

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(100)


class TestPreviousValue(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(grid=NoGrid()))},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        self.adapter = PreviousValue()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter
        self.adapter.get_info(Info(grid=NoGrid()))

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

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(datetime(2000, 1, 1, 0))

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(datetime(2000, 1, 4, 0))

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(100)


class TestLinearInterpolation(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(grid=NoGrid()))},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = LinearInterpolation()

        self.source.initialize()
        self.source.outputs["Step"] >> self.adapter
        self.adapter.get_info(Info(grid=NoGrid()))

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

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(datetime(2000, 1, 1, 0))

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(datetime(2000, 1, 4, 0))

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(100)


class TestLinearGridInterpolation(unittest.TestCase):
    def setUp(self):
        grid, _ = create_grid(10, 15, 0)
        self.source = CallbackGenerator(
            callbacks={
                "Grid": (lambda t: create_grid(10, 15, t.day - 1)[1], Info(grid=grid))
            },
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = LinearInterpolation()

        self.source.initialize()
        self.source.outputs["Grid"] >> self.adapter
        self.adapter.get_info(Info(grid=grid))

        self.source.connect()
        self.source.validate()

    def test_linear_grid_interpolation(self):
        self.assertEqual(
            tools.get_magnitued(self.adapter.get_data(datetime(2000, 1, 1, 0)))[
                0, 2, 3
            ],
            0.0,
        )
        self.source.update()
        self.assertEqual(
            tools.get_magnitued(self.adapter.get_data(datetime(2000, 1, 1, 12)))[
                0, 2, 3
            ],
            0.5,
        )
        self.assertEqual(
            tools.get_magnitued(self.adapter.get_data(datetime(2000, 1, 2, 0)))[
                0, 2, 3
            ],
            1.0,
        )
        self.source.update()
        self.assertEqual(
            tools.get_magnitued(self.adapter.get_data(datetime(2000, 1, 2, 12)))[
                0, 2, 3
            ],
            1.5,
        )
        self.assertEqual(
            tools.get_magnitued(self.adapter.get_data(datetime(2000, 1, 3, 0)))[
                0, 2, 3
            ],
            2.0,
        )

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(datetime(2000, 1, 1, 0))

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(datetime(2000, 1, 4, 0))

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(100)


class TestLinearIntegration(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(grid=NoGrid(), units="m"))},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = LinearIntegration()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter
        self.adapter.get_info(Info(grid=NoGrid()))

        self.source.connect()
        self.source.validate()

    def test_linear_integration(self):
        self.source.update()
        self.assertEqual(
            tools.get_magnitued(self.adapter.get_data(datetime(2000, 1, 1, 12))), 0.25
        )
        self.assertEqual(
            tools.get_magnitued(self.adapter.get_data(datetime(2000, 1, 2, 0))), 0.75
        )
        self.source.update()
        self.source.update()
        self.assertEqual(
            tools.get_magnitued(self.adapter.get_data(datetime(2000, 1, 4, 0))), 2.0
        )

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(datetime(2000, 1, 2, 0))

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(datetime(2000, 1, 5, 0))

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(100)


class TestLinearGridIntegration(unittest.TestCase):
    def setUp(self):
        grid, _ = create_grid(10, 15, 0)
        self.source = CallbackGenerator(
            callbacks={
                "Grid": (lambda t: create_grid(10, 15, t.day - 1)[1], Info(grid=grid))
            },
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = LinearIntegration()

        self.source.initialize()

        self.source.outputs["Grid"] >> self.adapter
        self.adapter.get_info(Info(grid=NoGrid()))

        self.source.connect()
        self.source.validate()

    def test_linear_grid_integration(self):
        self.source.update()
        self.assertEqual(
            tools.get_magnitued(self.adapter.get_data(datetime(2000, 1, 1, 12)))[
                0, 2, 3
            ],
            0.25,
        )
        self.assertEqual(
            tools.get_magnitued(self.adapter.get_data(datetime(2000, 1, 2, 0)))[
                0, 2, 3
            ],
            0.75,
        )
        self.source.update()
        self.source.update()
        self.assertEqual(
            tools.get_magnitued(self.adapter.get_data(datetime(2000, 1, 4, 0)))[
                0, 2, 3
            ],
            2.0,
        )

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(datetime(2000, 1, 2, 0))

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(datetime(2000, 1, 5, 0))

        with self.assertRaises(FinamTimeError) as context:
            self.adapter.get_data(100)


def create_grid(cols, rows, value):
    grid = UniformGrid((cols, rows), data_location="POINTS")

    data = np.full(shape=grid.data_shape, fill_value=value, order=grid.order)

    return grid, data


if __name__ == "__main__":
    unittest.main()
