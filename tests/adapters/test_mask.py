"""
Unit tests for the adapters.mask module.
"""

import unittest
from datetime import datetime, timedelta

import numpy as np
from numpy.testing import assert_allclose

import finam as fm
from finam import Info, UniformGrid
from finam import data as fmdata
from finam.components.generators import CallbackGenerator, StaticCallbackGenerator


class TestMasking(unittest.TestCase):
    def setUp(self):
        grid, data = create_grid(20, 10, 1.0)
        self.mask = np.full_like(data, False, dtype=bool)
        self.mask[0, :] = True

        self.source = CallbackGenerator(
            callbacks={
                "Grid": (lambda t: data, Info(grid=grid, mask=fm.Mask.NONE, units="m"))
            },
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.source.initialize()

        self.mask_source = CallbackGenerator(
            callbacks={
                "Grid": (lambda t: data, Info(grid=grid, mask=self.mask, units="m"))
            },
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.mask_source.initialize()

    def test_mask_specified(self):
        self.adapter = fm.adapters.Masking(mask=self.mask)
        self.source.outputs["Grid"] >> self.adapter

        self.adapter.get_info(Info(units=None))
        self.source.connect(datetime(2000, 1, 1))
        self.source.connect(datetime(2000, 1, 1))
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1), None)
        self.assertTrue(fmdata.is_masked_array(result))
        assert_allclose(result[0].mask, self.mask)

    def test_mask_from_upstream(self):
        self.adapter = fm.adapters.Masking(fill_value=0.0)
        self.source.outputs["Grid"] >> self.adapter

        with self.assertRaises(fm.FinamMetaDataError):
            self.adapter.get_info(Info(units=None, mask=None))
        self.adapter.get_info(Info(units=None, mask=self.mask))
        self.source.connect(datetime(2000, 1, 1))
        self.source.connect(datetime(2000, 1, 1))
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1), None)
        self.assertTrue(fmdata.is_masked_array(result))
        self.assertAlmostEqual(result.fill_value, 0.0)
        assert_allclose(result[0].mask, self.mask)

    def test_mask_from_upstream_flex(self):
        self.adapter = fm.adapters.Masking(fill_value=0.0)
        self.source.outputs["Grid"] >> self.adapter

        self.adapter.get_info(Info(units=None, mask=fm.Mask.FLEX))
        self.source.connect(datetime(2000, 1, 1))
        self.source.connect(datetime(2000, 1, 1))
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1), None)
        self.assertTrue(fmdata.is_masked_array(result))

    def test_sub_mask(self):
        self.adapter = fm.adapters.Masking(fill_value=0.0)
        self.source.outputs["Grid"] >> self.adapter
        mask = self.mask.copy()
        mask[-1, :] = True
        self.adapter.get_info(Info(units=None, mask=mask))
        self.source.connect(datetime(2000, 1, 1))
        self.source.connect(datetime(2000, 1, 1))
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1), None)
        self.assertTrue(fmdata.is_masked_array(result))
        self.assertAlmostEqual(result.fill_value, 0.0)
        assert_allclose(result[0].mask, mask)
        assert_allclose(result[0].magnitude[mask], 0.0)

    def test_sub_mask_fail(self):
        self.adapter = fm.adapters.Masking(fill_value=0.0)
        self.mask_source.outputs["Grid"] >> self.adapter
        mask = np.full_like(self.mask, False)
        mask[-1, :] = True
        self.assertFalse(fmdata.tools.is_sub_mask(self.mask, mask))
        with self.assertRaises(fm.FinamMetaDataError):
            self.adapter.get_info(Info(units=None, mask=mask))


class TestUnMasking(unittest.TestCase):
    def setUp(self):
        grid, data = create_grid(20, 10, 1.0)
        self.mask = np.full_like(data, False, dtype=bool)
        self.mask[0, :] = True

        self.source = CallbackGenerator(
            callbacks={
                "Grid": (lambda t: data, Info(grid=grid, mask=self.mask, units="m"))
            },
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.source.initialize()

    def test_unmask(self):
        self.adapter = fm.adapters.UnMasking(fill_value=0.0)
        self.source.outputs["Grid"] >> self.adapter

        self.adapter.get_info(Info(units=None, mask=fm.Mask.NONE))
        self.source.connect(datetime(2000, 1, 1))
        self.source.connect(datetime(2000, 1, 1))
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1), None)
        self.assertFalse(fmdata.is_masked_array(result))
        assert_allclose(result[0].magnitude[self.mask], 0.0)

    def test_unmask_with_none_mask(self):
        self.adapter = fm.adapters.Masking(fill_value=0.0)
        self.source.outputs["Grid"] >> self.adapter

        self.adapter.get_info(Info(units=None, mask=fm.Mask.NONE))
        self.source.connect(datetime(2000, 1, 1))
        self.source.connect(datetime(2000, 1, 1))
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1), None)
        self.assertFalse(fmdata.is_masked_array(result))
        assert_allclose(result[0].magnitude[self.mask], 0.0)


class TestClip(unittest.TestCase):
    def setUp(self):
        grid, data = create_grid(20, 10, 1.0)
        self.mask = np.full_like(data, False, dtype=bool)
        self.mask[0, :] = True

        self.source = CallbackGenerator(
            callbacks={
                "Grid": (lambda t: data, Info(grid=grid, mask=self.mask, units="m"))
            },
            start=datetime(2000, 1, 1),
            step=timedelta(1.0),
        )

        self.source.initialize()

    def test_clip(self):
        clip1 = fm.adapters.Clip(xlim=(3, 9), ylim=(2, 8))
        clip2 = fm.adapters.Clip(xlim=(3, 9), ylim=(2, 8))
        unst1 = fm.adapters.ToUnstructured()
        unst2 = fm.adapters.ToUnstructured()
        self.source.outputs["Grid"] >> clip1 >> unst1
        self.source.outputs["Grid"] >> unst2 >> clip2

        unst1.get_info(Info(units=None))
        clip2.get_info(Info(units=None))
        self.source.connect(datetime(2000, 1, 1))
        self.source.connect(datetime(2000, 1, 1))
        self.source.validate()

        res1 = unst1.get_data(datetime(2000, 1, 1), None)
        res2 = clip2.get_data(datetime(2000, 1, 1), None)

        assert_allclose(res1[0].magnitude, res2[0].magnitude)
        self.assertTrue(unst1.output_grid == clip2.output_grid)
        self.assertGreaterEqual(np.min(unst1.output_grid.points[:, 0]), 3)
        self.assertLessEqual(np.min(unst1.output_grid.points[:, 0]), 9)
        self.assertGreaterEqual(np.min(unst1.output_grid.points[:, 1]), 2)
        self.assertLessEqual(np.min(unst1.output_grid.points[:, 1]), 8)

    def test_clip_fail(self):
        clip_fail1 = fm.adapters.Clip(ylim=(20, 80))
        clip_fail2 = fm.adapters.Clip(ylim=(20, 80))
        clip_grid_fail = fm.adapters.Clip(ylim=(3, 9))
        unst = fm.adapters.ToUnstructured()
        grid = fm.UniformGrid((2, 3))
        self.source.outputs["Grid"] >> clip_fail1
        self.source.outputs["Grid"] >> unst >> clip_fail2
        self.source.outputs["Grid"] >> clip_grid_fail
        # ylim creates empty selection
        with self.assertRaises(fm.FinamMetaDataError):
            clip_fail1.get_info(Info(units=None))
        with self.assertRaises(fm.FinamMetaDataError):
            clip_fail2.get_info(Info(units=None))
        # wrong output grid
        with self.assertRaises(fm.FinamMetaDataError):
            clip_grid_fail.get_info(Info(units=None, grid=grid))

        static = StaticCallbackGenerator({"Grid": (lambda t: 0, Info())})
        static.initialize()
        clip_missing = fm.adapters.Clip()
        static["Grid"] >> clip_missing
        # no grid
        with self.assertRaises(fm.FinamMetaDataError):
            clip_missing.get_info(Info(units=None))

        static = StaticCallbackGenerator(
            {"Grid": (lambda t: 0, Info(grid=fm.NoGrid()))}
        )
        static.initialize()
        clip_missing = fm.adapters.Clip()
        static["Grid"] >> clip_missing
        # wrong grid

        with self.assertRaises(fm.FinamMetaDataError):
            clip_missing.get_info(Info(units=None))

        grid = fm.UniformGrid((2, 3))
        static = StaticCallbackGenerator(
            {"Grid": (lambda t: 0, Info(grid=grid, mask=None))}
        )
        static.initialize()
        clip_missing = fm.adapters.Clip()
        static["Grid"] >> clip_missing
        # missing mask
        with self.assertRaises(fm.FinamMetaDataError):
            clip_missing.get_info(Info(units=None))


def create_grid(cols, rows, value):
    grid = UniformGrid((cols, rows), data_location="POINTS")
    data = np.full(shape=grid.data_shape, fill_value=value, order=grid.order)

    return grid, data


if __name__ == "__main__":
    unittest.main()
