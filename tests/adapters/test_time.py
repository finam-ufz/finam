"""
Unit tests for the adapters.time module.
"""

import unittest
from datetime import datetime, timedelta

import numpy as np
import pint
from numpy.testing import assert_array_equal

from finam import FinamTimeError, Info, NoGrid, UniformGrid
from finam import data as tools
from finam.adapters.time import (
    DelayFixed,
    DelayToPull,
    DelayToPush,
    LinearTime,
    NextTime,
    PreviousTime,
    StackTime,
    StepTime,
    interpolate,
    interpolate_step,
)
from finam.components import CallbackGenerator

reg = pint.UnitRegistry(force_ndarray_like=True)


class TestDelayToPush(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)

        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=start,
            step=timedelta(days=1),
        )

        self.adapter = DelayToPush()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect(start)
        self.source.connect(start)
        self.source.validate()

    def test_delay_to_push(self):
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0), None), 0.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 5, 0), None), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0), None), 0.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 5, 0), None), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 5, 0), None), 2.0)


class TestDelayToPull(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)

        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day, Info(None, grid=NoGrid()))},
            start=start,
            step=timedelta(days=1),
        )

        self.adapter = DelayToPull(steps=2, additional_delay=timedelta(days=0.8))

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect(start)
        self.source.connect(start)
        self.source.validate()

    def test_delay_to_pull(self):
        for _ in range(10):
            self.source.update()

        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0), None), 1)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 0), None), 1)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 3, 0), None), 1)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 4, 0), None), 1)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 8, 0), None), 2)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 12, 0), None), 3)


class TestDelayFixed(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)
        self.last_pull = None

        def callback(t):
            return t.day - 1

        self.source = CallbackGenerator(
            callbacks={"Step": (callback, Info(None, grid=NoGrid()))},
            start=start,
            step=timedelta(days=1),
        )

        self.adapter = DelayFixed(delay=timedelta(days=10))

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect(start)
        self.source.connect(start)
        self.source.validate()

    def test_fixed_delay(self):
        data = self.adapter.get_data(datetime(2000, 1, 1), None)
        self.assertEqual(data, 0)

        self.source.update()
        self.source.update()

        data = self.adapter.get_data(datetime(2000, 1, 5), None)
        self.assertEqual(data, 0)

        for _ in range(20):
            self.source.update()

        data = self.adapter.get_data(datetime(2000, 1, 10), None)
        self.assertEqual(data, 0)

        data = self.adapter.get_data(datetime(2000, 1, 11), None)
        self.assertEqual(data, 0)

        data = self.adapter.get_data(datetime(2000, 1, 12), None)
        self.assertEqual(data, 1)

        data = self.adapter.get_data(datetime(2000, 1, 20), None)
        self.assertEqual(data, 9)


class TestNextValue(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=start,
            step=timedelta(1.0),
        )

        self.adapter = NextTime()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect(start)
        self.source.connect(start)
        self.source.validate()

    def test_next_value(self):
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0), None), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 12), None), 1.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 0), None), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 12), None), 2.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 3, 0), None), 2.0)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(datetime(2000, 1, 4, 0), None)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(100, None)


class TestPreviousValue(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=start,
            step=timedelta(days=1),
        )

        self.adapter = PreviousTime()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter
        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect(start)
        self.source.connect(start)
        self.source.validate()

    def test_previous_value(self):
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0), None), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 12), None), 0.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 0), None), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 12), None), 1.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 3, 0), None), 2.0)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(datetime(2000, 1, 1, 0), None)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(datetime(2000, 1, 4, 0), None)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(100, None)


class TestInterpolation(unittest.TestCase):
    def test_linear(self):
        self.assertEqual(interpolate(0.0, 10.0, 0.0), 0.0)
        self.assertEqual(interpolate(0.0, 10.0, 1.0), 10.0)
        self.assertEqual(interpolate(0.0, 10.0, 0.1), 1.0)

    def test_step(self):
        self.assertEqual(interpolate_step(0.0, 10.0, 0.0, 0.3), 0.0)
        self.assertEqual(interpolate_step(0.0, 10.0, 1.0, 0.3), 10.0)
        self.assertEqual(interpolate_step(0.0, 10.0, 0.1, 0.3), 0.0)
        self.assertEqual(interpolate_step(0.0, 10.0, 0.3, 0.3), 0.0)
        self.assertEqual(interpolate_step(0.0, 10.0, 0.31, 0.3), 10.0)
        self.assertEqual(interpolate_step(0.0, 10.0, 1.0, 0.3), 10.0)


class TestStepInterpolation(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=start,
            step=timedelta(days=10.0),
        )

        self.adapter = StepTime(step=0.3)

        self.source.initialize()
        self.source.outputs["Step"] >> self.adapter
        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect(start)
        self.source.connect(start)
        self.source.validate()

    def test_step_interpolation(self):
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0), None), 0.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 0), None), 0.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 3, 0), None), 0.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 4, 0), None), 0.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 5, 0), None), 10.0)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(datetime(2000, 1, 12, 0), None)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(100, None)


class TestLinearInterpolation(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=start,
            step=timedelta(1.0),
        )

        self.adapter = LinearTime()

        self.source.initialize()
        self.source.outputs["Step"] >> self.adapter
        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect(start)
        self.source.connect(start)
        self.source.validate()

    def test_linear_interpolation(self):
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0), None), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 12), None), 0.5)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 0), None), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 2, 12), None), 1.5)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 3, 0), None), 2.0)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(datetime(2000, 1, 1, 0), None)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(datetime(2000, 1, 4, 0), None)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(100, None)


class TestLinearGridInterpolation(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)
        grid, _ = create_grid(10, 15, 0)
        self.source = CallbackGenerator(
            callbacks={
                "Grid": (
                    lambda t: create_grid(10, 15, t.day - 1)[1],
                    Info(None, grid=grid),
                )
            },
            start=start,
            step=timedelta(1.0),
        )

        self.adapter = LinearTime()

        self.source.initialize()
        self.source.outputs["Grid"] >> self.adapter
        self.adapter.get_info(Info(None, grid=grid))

        self.source.connect(start)
        self.source.connect(start)
        self.source.validate()

    def test_linear_grid_interpolation(self):
        self.assertEqual(
            tools.get_magnitude(self.adapter.get_data(datetime(2000, 1, 1, 0), None))[
                0, 2, 3
            ],
            0.0,
        )
        self.source.update()
        self.assertEqual(
            tools.get_magnitude(self.adapter.get_data(datetime(2000, 1, 1, 12), None))[
                0, 2, 3
            ],
            0.5,
        )
        self.assertEqual(
            tools.get_magnitude(self.adapter.get_data(datetime(2000, 1, 2, 0), None))[
                0, 2, 3
            ],
            1.0,
        )
        self.source.update()
        self.assertEqual(
            tools.get_magnitude(self.adapter.get_data(datetime(2000, 1, 2, 12), None))[
                0, 2, 3
            ],
            1.5,
        )
        self.assertEqual(
            tools.get_magnitude(self.adapter.get_data(datetime(2000, 1, 3, 0), None))[
                0, 2, 3
            ],
            2.0,
        )

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(datetime(2000, 1, 1, 0), None)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(datetime(2000, 1, 4, 0), None)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(100, None)


class TestTimeStack(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)
        grid, _ = create_grid(10, 15, 0)
        self.source = CallbackGenerator(
            callbacks={
                "Grid": (
                    lambda t: create_grid(10, 15, t.day - 1)[1],
                    Info(None, grid=grid),
                )
            },
            start=start,
            step=timedelta(1.0),
        )

        self.adapter = StackTime()

        self.source.initialize()

        self.source.outputs["Grid"] >> self.adapter
        self.adapter.get_info(Info(None, grid=grid))

        self.source.connect(start)
        self.source.connect(start)
        self.source.validate()

    def test_stack_time(self):
        self.source.update()
        self.source.update()
        self.source.update()

        data = self.adapter.get_data(datetime(2000, 1, 4), None)
        self.assertEqual(data.shape, (4, 10, 15))

        self.source.update()
        self.source.update()

        data = self.adapter.get_data(datetime(2000, 1, 6), None)
        self.assertEqual(data.shape, (3, 10, 15))


def create_grid(cols, rows, value):
    grid = UniformGrid((cols, rows), data_location="POINTS")

    data = np.full(shape=grid.data_shape, fill_value=value, order=grid.order)

    return grid, data


if __name__ == "__main__":
    unittest.main()
