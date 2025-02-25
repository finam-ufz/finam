"""
Unit tests for regridding with masked data.
"""

import unittest
from pathlib import Path

import numpy as np
from numpy.testing import assert_array_equal

from finam import Composition, FinamDataError, Info, Mask, UniformGrid, UnstructuredGrid
from finam import data as fdata
from finam.adapters.regrid import RegridLinear, RegridNearest
from finam.components import StaticSimplexNoise, debug


def get_mask(points, rad=1.5):
    return (points[:, 0] - 2.5) ** 2 + (points[:, 1] - 2) ** 2 > rad**2


class TestRegridMask(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        here = Path(__file__).parent
        points = np.loadtxt(here / "square_5x4" / "points.txt", dtype=float)
        cells = np.loadtxt(here / "square_5x4" / "cells.txt", dtype=int)
        types = np.loadtxt(here / "square_5x4" / "types.txt", dtype=int)

        self.in_grid = UnstructuredGrid(points, cells, types)
        self.out_grid = UniformGrid((25, 20), spacing=(0.2, 0.2))

        self.in_mask = get_mask(self.in_grid.cell_centers, rad=1.5)
        omask = get_mask(self.out_grid.cell_centers, rad=2.5)
        self.out_mask = fdata.from_compressed(
            omask, self.out_grid.data_shape, self.out_grid.order
        )

    def test_regrid_nearest_out_mask(self):
        in_info = Info(grid=self.in_grid, units="", mask=self.in_mask)
        source = StaticSimplexNoise(in_info, 0.15, 3, 0.5)
        sink = debug.DebugPushConsumer({"Input": Info()})
        regrid = RegridNearest(out_grid=self.out_grid, out_mask=self.out_mask)
        composition = Composition([source, sink])

        (source.outputs["Noise"] >> regrid >> sink.inputs["Input"])
        composition.connect()

        info = sink.inputs["Input"].info
        data = sink.data["Input"][0, ...]
        assert_array_equal(info.mask, data.mask)
        assert_array_equal(info.mask, self.out_mask)

        i_data = source.outputs["Noise"].data[0][1].magnitude.compressed()
        o_data = data.magnitude.compressed()
        self.assertAlmostEqual(i_data.mean(), o_data.mean(), 2)

    def test_regrid_nearest_filled(self):
        in_info = Info(grid=self.in_grid, units="", mask=self.in_mask)
        source = StaticSimplexNoise(in_info, 0.15, 3, 0.5)
        sink = debug.DebugPushConsumer({"Input": Info()})
        regrid = RegridNearest(out_grid=self.out_grid, out_mask=Mask.NONE)
        composition = Composition([source, sink])

        (source.outputs["Noise"] >> regrid >> sink.inputs["Input"])
        composition.connect()

        info = sink.inputs["Input"].info
        data = sink.data["Input"][0, ...].magnitude
        self.assertEqual(info.mask, Mask.NONE)
        self.assertFalse(fdata.is_masked_array(data))

        i_data = source.outputs["Noise"].data[0][1].magnitude.compressed()
        self.assertAlmostEqual(i_data.mean(), data.mean(), 1)

    def test_regrid_linear_determine_mask(self):
        in_info = Info(grid=self.in_grid, units="", mask=self.in_mask)
        source = StaticSimplexNoise(in_info, 0.15, 3, 0.5)
        sink = debug.DebugPushConsumer({"Input": Info()})
        regrid = RegridLinear(
            out_grid=self.out_grid, fill_with_nearest=False, out_mask=None
        )
        composition = Composition([source, sink])

        (source.outputs["Noise"] >> regrid >> sink.inputs["Input"])
        composition.connect()

        info = sink.inputs["Input"].info
        data = sink.data["Input"][0, ...]
        assert_array_equal(info.mask, data.mask)
        self.assertEqual(np.sum(data.mask), 306)

        i_data = source.outputs["Noise"].data[0][1].magnitude.compressed()
        o_data = data.magnitude.compressed()
        self.assertAlmostEqual(i_data.mean(), o_data.mean(), 2)

    def test_regrid_linear_error_domain(self):
        in_info = Info(grid=self.in_grid, units="", mask=self.in_mask)
        source = StaticSimplexNoise(in_info, 0.15, 3, 0.5)
        sink = debug.DebugPushConsumer({"Input": Info()})
        regrid = RegridLinear(
            out_grid=self.out_grid, fill_with_nearest=False, out_mask=Mask.NONE
        )
        composition = Composition([source, sink])

        (source.outputs["Noise"] >> regrid >> sink.inputs["Input"])

        # not covering domain without fill
        with self.assertRaises(FinamDataError):
            composition.connect()

    def test_regrid_linear_filled(self):
        in_info = Info(grid=self.in_grid, units="", mask=self.in_mask)
        source = StaticSimplexNoise(in_info, 0.15, 3, 0.5)
        sink = debug.DebugPushConsumer({"Input": Info()})
        regrid = RegridLinear(
            out_grid=self.out_grid, fill_with_nearest=True, out_mask=Mask.NONE
        )
        composition = Composition([source, sink])

        (source.outputs["Noise"] >> regrid >> sink.inputs["Input"])
        composition.connect()

        info = sink.inputs["Input"].info
        data = sink.data["Input"][0, ...].magnitude
        self.assertEqual(info.mask, Mask.NONE)
        self.assertFalse(fdata.is_masked_array(data))

        i_data = source.outputs["Noise"].data[0][1].magnitude.compressed()
        self.assertAlmostEqual(i_data.mean(), data.mean(), 1)

    def test_regrid_linear_filled_mask(self):
        in_info = Info(grid=self.in_grid, units="", mask=self.in_mask)
        source = StaticSimplexNoise(in_info, 0.15, 3, 0.5)
        sink = debug.DebugPushConsumer({"Input": Info()})
        regrid = RegridLinear(
            out_grid=self.out_grid, fill_with_nearest=True, out_mask=self.out_mask
        )
        composition = Composition([source, sink])

        (source.outputs["Noise"] >> regrid >> sink.inputs["Input"])
        composition.connect()

        info = sink.inputs["Input"].info
        data = sink.data["Input"][0, ...]
        assert_array_equal(info.mask, data.mask)
        assert_array_equal(info.mask, self.out_mask)

        i_data = source.outputs["Noise"].data[0][1].magnitude.compressed()
        o_data = data.magnitude.compressed()
        self.assertAlmostEqual(i_data.mean(), o_data.mean(), 2)


if __name__ == "__main__":
    unittest.main()
