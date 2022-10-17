import unittest
from datetime import datetime, timedelta

from finam import Composition, Info, NoGrid
from finam.modules.generators import CallbackGenerator
from finam.modules.visual.time_series import TimeSeriesView


class TestTimeSeries(unittest.TestCase):
    def test_time_series(self):
        start = datetime(2000, 1, 1)

        gen1 = CallbackGenerator(
            callbacks={"Out": (lambda t: 0, Info(grid=NoGrid()))},
            start=start,
            step=timedelta(days=1),
        )
        gen2 = CallbackGenerator(
            callbacks={"Out": (lambda t: (t - start).days, Info(grid=NoGrid()))},
            start=start,
            step=timedelta(days=3),
        )

        series = TimeSeriesView(["Gen1", "Gen2"], start=start, step=timedelta(days=3))

        comp = Composition([gen1, gen2, series])
        comp.initialize()

        gen1.outputs["Out"] >> series.inputs["Gen1"]
        gen2.outputs["Out"] >> series.inputs["Gen2"]

        comp.run(t_max=datetime(2000, 1, 15))

    def test_time_fail(self):
        with self.assertRaises(ValueError):
            _series = TimeSeriesView(["Gen1", "Gen2"], start=0, step=timedelta(days=3))
        with self.assertRaises(ValueError):
            _series = TimeSeriesView(
                ["Gen1", "Gen2"], start=datetime(2000, 1, 1), step=0
            )
