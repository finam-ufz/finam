"""
Unit tests for masking adapter.
"""
import unittest
from datetime import datetime, timedelta

import numpy as np

from finam import (
    Composition,
    EsriGrid,
    Info,
)
from finam.adapters.masking import Masking
from finam.modules import debug, generators


class TestMasking(unittest.TestCase):
    def test_masking(self):
        time = datetime(2000, 1, 1)

        mask = [
            [True, False, True],
            [False, False, True],
            [False, False, False],
            [True, False, False],
        ]

        in_grid = EsriGrid(ncols=3, nrows=4, order="F")
        out_grid = EsriGrid(ncols=3, nrows=4, mask=mask, order="F")

        in_info = Info(time=time, grid=in_grid, units="m")

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0
        in_data.data[0, 1] = 2.0

        source = generators.CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = debug.DebugConsumer(
            {"Input": Info(None, grid=out_grid, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink], log_level="DEBUG")
        composition.initialize()

        source.outputs["Output"] >> Masking() >> sink.inputs["Input"]

        composition.connect()
        self.assertTrue(np.isnan(sink.data["Input"][0][0, 0]))
        self.assertAlmostEqual(sink.data["Input"][0][0, 1].magnitude, 2.0)
        print(sink.data["Input"][0])


if __name__ == "__main__":
    unittest.main()
