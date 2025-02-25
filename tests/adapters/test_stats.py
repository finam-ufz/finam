import unittest
from datetime import datetime, timedelta

import numpy as np
from numpy.testing import assert_allclose

import finam as fm


class TestHistogram(unittest.TestCase):
    def test_histogram(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((15, 12)),
            units="m",
        )

        source = fm.components.SimplexNoise(info=in_info)
        sink = fm.components.DebugConsumer(
            {"Input": fm.Info(None, grid=None, units=None)},
            start=time,
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, sink])

        (
            source.outputs["Noise"]
            >> fm.adapters.Histogram(lower=-1, upper=1, bins=20)
            >> sink.inputs["Input"]
        )

        composition.connect()

        data = sink.data["Input"]
        self.assertEqual(data.shape, (1, 20))
        self.assertEqual(data.sum(), 11 * 14)
        self.assertEqual(fm.data.get_units(data), fm.UNITS.dimensionless)

        composition.run(end_time=datetime(2000, 1, 10))


if __name__ == "__main__":
    unittest.main()
