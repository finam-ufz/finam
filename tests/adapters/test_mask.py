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
from finam.components.generators import CallbackGenerator


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

        self.adapter.get_info(Info(units=None, mask=self.mask))
        self.source.connect(datetime(2000, 1, 1))
        self.source.connect(datetime(2000, 1, 1))
        self.source.validate()

        result = self.adapter.get_data(datetime(2000, 1, 1), None)
        self.assertTrue(fmdata.is_masked_array(result))
        self.assertAlmostEqual(result.fill_value, 0.0)
        assert_allclose(result[0].mask, self.mask)

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


def create_grid(cols, rows, value):
    grid = UniformGrid((cols, rows), data_location="POINTS")

    data = np.full(shape=grid.data_shape, fill_value=value, order=grid.order)

    return grid, data


if __name__ == "__main__":
    unittest.main()
