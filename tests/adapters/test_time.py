"""
Unit tests for the adapters.time module.
"""
import unittest
from datetime import datetime, timedelta

import numpy as np
import pint
from numpy.testing import assert_allclose, assert_array_equal

import finam as fm
from finam import FinamTimeError, Info, NoGrid, UniformGrid
from finam import data as tools
from finam.adapters.time import (
    DelayFixed,
    DelayToPull,
    DelayToPush,
    IntegrateTime,
    LinearTime,
    NextTime,
    PreviousTime,
    StackTime,
    StepTime,
    interpolate,
    interpolate_step,
)
from finam.modules import CallbackGenerator, DebugConsumer

reg = pint.UnitRegistry(force_ndarray_like=True)


class TestDelayToPush(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        self.adapter = DelayToPush()

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect()
        self.source.connect()
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
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day, Info(None, grid=NoGrid()))},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        self.adapter = DelayToPull(steps=2, additional_delay=timedelta(days=0.8))

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect()
        self.source.connect()
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
        self.last_pull = None

        def callback(t):
            return t.day - 1

        self.source = CallbackGenerator(
            callbacks={"Step": (callback, Info(None, grid=NoGrid()))},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        self.adapter = DelayFixed(delay=timedelta(days=10))

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter

        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect()
        self.source.connect()
        self.source.validate()

    def test_fixed_delay(self):
        data = self.adapter.get_data(datetime(2000, 1, 1), None)
        self.assertEqual(tools.get_time(data)[0], datetime(2000, 1, 1))
        self.assertEqual(tools.get_data(data), 0)

        self.source.update()
        self.source.update()

        data = self.adapter.get_data(datetime(2000, 1, 5), None)
        self.assertEqual(tools.get_time(data)[0], datetime(2000, 1, 1))
        self.assertEqual(tools.get_data(data), 0)

        for _ in range(20):
            self.source.update()

        data = self.adapter.get_data(datetime(2000, 1, 10), None)
        self.assertEqual(tools.get_time(data)[0], datetime(2000, 1, 1))
        self.assertEqual(tools.get_data(data), 0)

        data = self.adapter.get_data(datetime(2000, 1, 11), None)
        self.assertEqual(tools.get_time(data)[0], datetime(2000, 1, 1))
        self.assertEqual(tools.get_data(data), 0)

        data = self.adapter.get_data(datetime(2000, 1, 12), None)
        self.assertEqual(tools.get_time(data)[0], datetime(2000, 1, 2))
        self.assertEqual(tools.get_data(data), 1)

        data = self.adapter.get_data(datetime(2000, 1, 20), None)
        self.assertEqual(tools.get_time(data)[0], datetime(2000, 1, 10))
        self.assertEqual(tools.get_data(data), 9)


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
        self.source = CallbackGenerator(
            callbacks={"Step": (lambda t: t.day - 1, Info(None, grid=NoGrid()))},
            start=datetime(2000, 1, 1),
            step=timedelta(days=10.0),
        )

        self.adapter = StepTime(step=0.3)

        self.source.initialize()
        self.source.outputs["Step"] >> self.adapter
        self.adapter.get_info(Info(None, grid=NoGrid()))

        self.source.connect()
        self.source.connect()
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


class TestLinearIntegrationSum(unittest.TestCase):
    def setUp(self):

        self.data = {
            "In_lin": [],
            "In_00": [],
            "In_05": [],
            "In_10": [],
        }

        def callback(n, d, t):
            self.data[n].append((t, d))

        self.source = CallbackGenerator(
            callbacks={
                "Step": (
                    lambda t: t.day * fm.UNITS.Unit("mm/d"),
                    Info(None, grid=NoGrid(), units="mm/d"),
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        self.adapter_lin = IntegrateTime(sum=True, initial_interval=timedelta(days=1))
        self.adapter_00 = IntegrateTime(
            step=0.0, sum=True, initial_interval=timedelta(days=1)
        )
        self.adapter_05 = IntegrateTime(
            step=0.5, sum=True, initial_interval=timedelta(days=1)
        )
        self.adapter_10 = IntegrateTime(
            step=1.0, sum=True, initial_interval=timedelta(days=1)
        )

        self.consumer = DebugConsumer(
            inputs={
                "In_lin": fm.Info(time=None, grid=NoGrid(), units="mm"),
                "In_00": fm.Info(time=None, grid=NoGrid(), units="mm"),
                "In_05": fm.Info(time=None, grid=NoGrid(), units="mm"),
                "In_10": fm.Info(time=None, grid=NoGrid(), units="mm"),
            },
            callbacks={
                "In_lin": callback,
                "In_00": callback,
                "In_05": callback,
                "In_10": callback,
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=2),
        )

        self.comp = fm.Composition([self.source, self.consumer])
        self.comp.initialize()

        self.source["Step"] >> self.adapter_lin >> self.consumer["In_lin"]
        self.source["Step"] >> self.adapter_00 >> self.consumer["In_00"]
        self.source["Step"] >> self.adapter_05 >> self.consumer["In_05"]
        self.source["Step"] >> self.adapter_10 >> self.consumer["In_10"]

    def test_linear_integration_sum(self):
        self.comp.run(t_max=datetime(2000, 1, 10))

        mm = fm.UNITS.Unit("mm")

        res = [d.item(0) for t, d in self.data["In_lin"]]
        exp = [1 * mm, 4 * mm, 8 * mm, 12 * mm, 16 * mm, 20 * mm]

        for r, e in zip(res, exp):
            self.assertEqual(r.units, e.units)
            self.assertAlmostEqual(r.magnitude, e.magnitude)

        res = [d.item(0) for t, d in self.data["In_05"]]
        exp = [1 * mm, 4 * mm, 8 * mm, 12 * mm, 16 * mm, 20 * mm]

        for r, e in zip(res, exp):
            self.assertEqual(r.units, e.units)
            self.assertAlmostEqual(r.magnitude, e.magnitude)

        res = [d.item(0) for t, d in self.data["In_00"]]
        exp = [1 * mm, 5 * mm, 9 * mm, 13 * mm, 17 * mm, 21 * mm]

        for r, e in zip(res, exp):
            self.assertEqual(r.units, e.units)
            self.assertAlmostEqual(r.magnitude, e.magnitude)

        res = [d.item(0) for t, d in self.data["In_10"]]
        exp = [1 * mm, 3 * mm, 7 * mm, 11 * mm, 15 * mm, 19 * mm]

        for r, e in zip(res, exp):
            self.assertEqual(r.units, e.units)
            self.assertAlmostEqual(r.magnitude, e.magnitude)


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
        self.adapter.get_info(Info(None, grid=grid))

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
        self.adapter.get_info(Info(None, grid=grid))

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
