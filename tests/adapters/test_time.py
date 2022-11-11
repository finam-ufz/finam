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
    ExtrapolateTime,
    IntegrateTime,
    LinearTime,
    NextTime,
    PreviousTime,
    StackTime,
)
from finam.modules.generators import CallbackGenerator

reg = pint.UnitRegistry(force_ndarray_like=True)


class TestExtrapolateTime(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        self.adapter = ExtrapolateTime()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect()
        self.source.connect()
        self.source.validate()

    def test_extrapolate(self):
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0), None), 0.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 5, 0), None), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 1, 0), None), 0.0)
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 5, 0), None), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(datetime(2000, 1, 5, 0), None), 2.0)


class TestExtrapolateTimeFixed(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        self.adapter = ExtrapolateTime(last_pull=True, force_last=True)

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect()
        self.source.connect()
        self.source.validate()

    def test_extrapolate(self):
        data = self.adapter.get_data(datetime(2000, 1, 5), None)
        self.source.update()
        self.source.update()

        self.assertEqual(tools.get_time(data)[0], datetime(2000, 1, 5))

        self.source.update()
        self.source.update()

        data = self.adapter.get_data(datetime(2000, 1, 10), None)
        self.assertEqual(tools.get_time(data)[0], datetime(2000, 1, 10))

    def test_extrapolate_fail(self):
        data = self.adapter.get_data(datetime(2000, 1, 5), None)
        self.source.update()
        self.source.update()

        self.assertEqual(tools.get_time(data)[0], datetime(2000, 1, 5))

        self.source.update()

        with self.assertRaises(FinamTimeError):
            _data = self.adapter.get_data(datetime(2000, 1, 10), None)


class TestNextValue(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = NextTime()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect()
        self.source.connect()
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
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        self.adapter = PreviousTime()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter
        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect()
        self.source.connect()
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


class TestLinearInterpolation(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = LinearTime()

        self.source.initialize()
        self.source.outputs["Step"] >> self.adapter
        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect()
        self.source.connect()
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
        grid, _ = create_grid(10, 15, 0)
        self.source = CallbackGenerator(
            callbacks={
                "Grid": (
                    lambda t: create_grid(10, 15, t.day - 1)[1],
                    Info(None, grid=grid),
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = LinearTime()

        self.source.initialize()
        self.source.outputs["Grid"] >> self.adapter
        self.adapter.get_info(Info(None, grid=grid))

        self.source.connect()
        self.source.connect()
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


class TestLinearIntegration(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={
                "Step": (lambda t: t.day - 1, Info(None, grid=NoGrid(), units="m"))
            },
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = IntegrateTime()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter
        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect()
        self.source.connect()
        self.source.validate()

    def test_linear_integration(self):
        self.source.update()
        self.assertEqual(
            tools.get_magnitude(self.adapter.get_data(datetime(2000, 1, 1, 12), None)),
            0.25,
        )
        self.assertEqual(
            tools.get_magnitude(self.adapter.get_data(datetime(2000, 1, 2, 0), None)),
            0.75,
        )
        self.source.update()
        self.source.update()
        self.assertEqual(
            tools.get_magnitude(self.adapter.get_data(datetime(2000, 1, 4, 0), None)),
            2.0,
        )

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(datetime(2000, 1, 1, 0), None)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(datetime(2000, 1, 5, 0), None)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(100, None)


class TestLinearGridIntegration(unittest.TestCase):
    def setUp(self):
        grid, _ = create_grid(10, 15, 0)
        self.source = CallbackGenerator(
            callbacks={
                "Grid": (
                    lambda t: create_grid(10, 15, t.day - 1)[1],
                    Info(None, grid=grid),
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = IntegrateTime()

        self.source.initialize()

        self.source.outputs["Grid"] >> self.adapter
        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect()
        self.source.connect()
        self.source.validate()

    def test_linear_grid_integration(self):
        self.source.update()
        self.assertEqual(
            tools.get_magnitude(self.adapter.get_data(datetime(2000, 1, 1, 12), None))[
                0, 2, 3
            ],
            0.25,
        )
        self.assertEqual(
            tools.get_magnitude(self.adapter.get_data(datetime(2000, 1, 2, 0), None))[
                0, 2, 3
            ],
            0.75,
        )
        self.source.update()
        self.source.update()
        self.assertEqual(
            tools.get_magnitude(self.adapter.get_data(datetime(2000, 1, 4, 0), None))[
                0, 2, 3
            ],
            2.0,
        )

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(datetime(2000, 1, 1, 0), None)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(datetime(2000, 1, 5, 0), None)

        with self.assertRaises(FinamTimeError):
            self.adapter.get_data(100, None)


class TestTimeStack(unittest.TestCase):
    def setUp(self):
        grid, _ = create_grid(10, 15, 0)
        self.source = CallbackGenerator(
            callbacks={
                "Grid": (
                    lambda t: create_grid(10, 15, t.day - 1)[1],
                    Info(None, grid=grid),
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.adapter = StackTime()

        self.source.initialize()

        self.source.outputs["Grid"] >> self.adapter
        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect()
        self.source.connect()
        self.source.validate()

    def test_stack_time(self):
        self.source.update()
        self.source.update()
        self.source.update()

        data = self.adapter.get_data(datetime(2000, 1, 4), None)
        self.assertEqual(data.shape, (4, 10, 15))
        assert_array_equal(
            data["time"],
            np.asarray(
                [
                    datetime(2000, 1, 1),
                    datetime(2000, 1, 2),
                    datetime(2000, 1, 3),
                    datetime(2000, 1, 4),
                ],
                dtype="datetime64[ns]",
            ),
        )

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
