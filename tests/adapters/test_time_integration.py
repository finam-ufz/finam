"""
Unit tests for the adapters.time module.
"""

import unittest
from datetime import datetime, timedelta

import numpy as np
import pint

import finam as fm
from finam import FinamTimeError, Info, NoGrid, UniformGrid
from finam import data as tools
from finam.adapters.time_integration import AvgOverTime, SumOverTime
from finam.components import CallbackGenerator, DebugConsumer

reg = pint.UnitRegistry(force_ndarray_like=True)


class TestAvgOverTime(unittest.TestCase):
    def init(self, step):
        start = datetime(2000, 1, 1)

        self.source = CallbackGenerator(
            callbacks={
                "Step": (lambda t: t.day - 1, Info(None, grid=NoGrid(), units="m"))
            },
            start=start,
            step=timedelta(1.0),
        )

        self.adapter = AvgOverTime(step=step)

        self.source.initialize()

        self.source.outputs["Step"] >> self.adapter
        self.adapter.get_info(Info(None, grid=NoGrid(), units=None))

        self.source.connect(start)
        self.source.connect(start)
        self.source.validate()

    def test_avg_over_time(self):
        self.init(None)

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

    def test_avg_step_over_time(self):
        self.init(0.25)

        self.source.update()
        self.source.update()

        data = self.adapter.get_data(datetime(2000, 1, 1, 4), None)
        self.assertAlmostEqual(tools.get_magnitude(data).item(), 0.0)

        data = self.adapter.get_data(datetime(2000, 1, 1, 7), None)
        self.assertAlmostEqual(tools.get_magnitude(data).item(), 1 / 3)

        data = self.adapter.get_data(datetime(2000, 1, 1, 20), None)
        self.assertAlmostEqual(tools.get_magnitude(data).item(), 1)

        data = self.adapter.get_data(datetime(2000, 1, 2, 4), None)
        self.assertAlmostEqual(tools.get_magnitude(data).item(), 1)

        data = self.adapter.get_data(datetime(2000, 1, 2, 8), None)
        self.assertAlmostEqual(tools.get_magnitude(data).item(), 1.5)


class TestGridAvgOverTime(unittest.TestCase):
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

        self.adapter = AvgOverTime()

        self.source.initialize()

        self.source.outputs["Grid"] >> self.adapter
        self.adapter.get_info(Info(None, grid=grid, units=None))

        self.source.connect(start)
        self.source.connect(start)
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


class TestSumOverTime(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)

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
            start=start,
            step=timedelta(days=1),
        )
        self.adapter_lin = SumOverTime(step=None)
        self.adapter_00 = SumOverTime(step=0.0)
        self.adapter_05 = SumOverTime(step=0.5)
        self.adapter_10 = SumOverTime(step=1.0)

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
            start=start,
            step=timedelta(days=2),
        )

        self.comp = fm.Composition([self.source, self.consumer])

        self.source["Step"] >> self.adapter_lin >> self.consumer["In_lin"]
        self.source["Step"] >> self.adapter_00 >> self.consumer["In_00"]
        self.source["Step"] >> self.adapter_05 >> self.consumer["In_05"]
        self.source["Step"] >> self.adapter_10 >> self.consumer["In_10"]

    def test_sum_over_time(self):
        self.comp.run(end_time=datetime(2000, 1, 10))

        mm = fm.UNITS.Unit("mm")

        res = [d.item(0) for t, d in self.data["In_lin"]]
        exp = [0 * mm, 4 * mm, 8 * mm, 12 * mm, 16 * mm, 20 * mm]

        for r, e in zip(res, exp):
            self.assertEqual(r.units, e.units)
            self.assertAlmostEqual(r.magnitude, e.magnitude)

        res = [d.item(0) for t, d in self.data["In_05"]]
        exp = [0 * mm, 4 * mm, 8 * mm, 12 * mm, 16 * mm, 20 * mm]

        for r, e in zip(res, exp):
            self.assertEqual(r.units, e.units)
            self.assertAlmostEqual(r.magnitude, e.magnitude)

        res = [d.item(0) for t, d in self.data["In_00"]]
        exp = [0 * mm, 5 * mm, 9 * mm, 13 * mm, 17 * mm, 21 * mm]

        for r, e in zip(res, exp):
            self.assertEqual(r.units, e.units)
            self.assertAlmostEqual(r.magnitude, e.magnitude)

        res = [d.item(0) for t, d in self.data["In_10"]]
        exp = [0 * mm, 3 * mm, 7 * mm, 11 * mm, 15 * mm, 19 * mm]

        for r, e in zip(res, exp):
            self.assertEqual(r.units, e.units)
            self.assertAlmostEqual(r.magnitude, e.magnitude)


class TestAbsSumOverTime(unittest.TestCase):
    def setUp(self):
        start = datetime(2000, 1, 1)

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
                    lambda t: 0.5 * (t.day + 1) * fm.UNITS.Unit("mm"),
                    Info(None, grid=NoGrid(), units="mm"),
                )
            },
            start=start,
            step=timedelta(days=2),
        )
        self.adapter_lin = SumOverTime(step=None, per_time=False)
        self.adapter_00 = SumOverTime(step=0.0, per_time=False)
        self.adapter_05 = SumOverTime(step=0.5, per_time=False)
        self.adapter_10 = SumOverTime(step=1.0, per_time=False)

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
            start=start,
            step=timedelta(days=4),
        )

        self.comp = fm.Composition([self.source, self.consumer])

        self.source["Step"] >> self.adapter_lin >> self.consumer["In_lin"]
        self.source["Step"] >> self.adapter_00 >> self.consumer["In_00"]
        self.source["Step"] >> self.adapter_05 >> self.consumer["In_05"]
        self.source["Step"] >> self.adapter_10 >> self.consumer["In_10"]

    def test_sum_over_time(self):
        self.comp.run(end_time=datetime(2000, 1, 20))

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


def create_grid(cols, rows, value):
    grid = UniformGrid((cols, rows), data_location="POINTS")

    data = np.full(shape=grid.data_shape, fill_value=value, order=grid.order)

    return grid, data


if __name__ == "__main__":
    unittest.main()
