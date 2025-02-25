"""
Unit tests for masked data.
"""

import unittest
from datetime import datetime, timedelta

import numpy as np

import finam as fm


def gen_masked(seed, shape):
    data = np.random.default_rng(seed).random(size=shape)
    mask = np.full(shape, False)
    # mask corners
    mask[0, 0] = mask[0, -1] = mask[-1, 0] = mask[-1, -1] = True
    return np.ma.masked_array(data, mask, fill_value=np.nan)


class TestMasked(unittest.TestCase):
    def test_rescale_masked(self):
        time = datetime(2000, 1, 1)

        in_info = fm.Info(
            time=time,
            grid=fm.UniformGrid(
                dims=(5, 4),
                spacing=(1.0, 1.0, 1.0),
                data_location=fm.Location.CELLS,
            ),
            units="m",
            missing_value=np.nan,
        )

        source = fm.components.generators.CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: gen_masked(t.toordinal(), in_info.grid.data_shape),
                    in_info,
                )
            },
            start=time,
            step=timedelta(days=1),
        )

        sink = fm.components.debug.DebugConsumer(
            {"Input": fm.Info(None, grid=None, units=None)},
            start=time,
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, sink])
        source.outputs["Output"] >> fm.adapters.Scale(scale=2.0) >> sink.inputs["Input"]
        composition.connect()

        self.assertTrue(sink.data["Input"][0][0, 0].mask)
        self.assertAlmostEqual(
            sink.data["Input"][0][1, 1].magnitude,
            2 * source.outputs["Output"].data[0][1][0][1, 1].magnitude,
        )

    def test_mask_tools(self):
        data = gen_masked(1234, (4, 3))
        mask = data.mask
        xdata = fm.data.quantify(data)

        sub_domain = np.full_like(data, fill_value=False, dtype=bool)
        self.assertFalse(fm.data.check_data_covers_domain(data, sub_domain))
        self.assertFalse(fm.data.check_data_covers_domain(xdata, sub_domain))

        sub_domain = data.mask
        self.assertTrue(fm.data.check_data_covers_domain(data, sub_domain))
        self.assertTrue(fm.data.check_data_covers_domain(xdata, sub_domain))

        sub_domain[0, 1] = True
        self.assertTrue(fm.data.check_data_covers_domain(data, sub_domain))
        self.assertTrue(fm.data.check_data_covers_domain(xdata, sub_domain))

        with self.assertRaises(ValueError):
            self.assertTrue(fm.data.check_data_covers_domain(data, [False, True]))
            self.assertTrue(fm.data.check_data_covers_domain(xdata, [False, True]))

        fdata = fm.data.filled(data)
        fxdata = fm.data.filled(xdata)

        self.assertTrue(fm.data.is_masked_array(data))
        self.assertTrue(fm.data.is_masked_array(xdata))
        self.assertTrue(fm.data.has_masked_values(data))
        self.assertTrue(fm.data.has_masked_values(xdata))

        self.assertFalse(fm.data.is_masked_array(fdata))
        self.assertFalse(fm.data.is_masked_array(fxdata))
        self.assertFalse(fm.data.has_masked_values(fdata))
        self.assertFalse(fm.data.has_masked_values(fxdata))

        np.testing.assert_allclose(data[mask], fdata[mask])
        np.testing.assert_allclose(xdata[mask].magnitude, fxdata[mask].magnitude)

        mfdata = fm.data.to_masked(fdata, mask=False)
        mfxdata = fm.data.to_masked(fxdata, mask=False)

        self.assertTrue(fm.data.is_masked_array(mfdata))
        self.assertTrue(fm.data.is_masked_array(mfxdata))
        self.assertFalse(fm.data.has_masked_values(mfdata))
        self.assertFalse(fm.data.has_masked_values(mfxdata))

        cdata_c = fm.data.to_compressed(data, order="C")
        cdata_f = fm.data.to_compressed(data, order="F")
        ucdata_c = fm.data.from_compressed(
            cdata_c, shape=data.shape, order="C", mask=mask
        )
        ucdata_f = fm.data.from_compressed(
            cdata_f, shape=data.shape, order="F", mask=mask
        )

        self.assertEqual(cdata_c.size, np.sum(~mask))
        self.assertEqual(cdata_f.size, np.sum(~mask))
        self.assertNotEqual(cdata_c[1], cdata_f[1])

        np.testing.assert_allclose(data[mask], ucdata_c[mask])
        np.testing.assert_allclose(data[mask], ucdata_f[mask])

        # more specific routines
        grid1 = fm.RectilinearGrid([(1.0, 2.0, 3.0, 4.0)])
        grid2 = fm.RectilinearGrid([(1.0, 2.0, 3.0)])
        grid3 = fm.RectilinearGrid([(1.0, 2.0, 3.0), (1.0, 2.0, 3.0)])
        mask1 = np.array((1, 0, 0), dtype=bool)
        mask2 = np.array((0, 0, 1), dtype=bool)
        mask3 = np.array((1, 0, 1), dtype=bool)
        mask4 = np.array((1, 1, 1), dtype=bool)
        mask5 = np.array((0, 0, 0), dtype=bool)
        mask6 = np.array((1, 0), dtype=bool)
        mask7 = np.array(((0, 1), (0, 1)), dtype=bool)
        data = np.ma.masked_array((10.0, 20.0, 30.0), mask1, fill_value=np.nan)

        # submask check
        self.assertFalse(fm.data.tools.is_sub_mask(mask1, mask2))
        self.assertFalse(fm.data.tools.is_sub_mask(mask1, np.ma.nomask))
        self.assertTrue(fm.data.tools.is_sub_mask(mask1, mask3))
        self.assertTrue(fm.data.tools.is_sub_mask(mask2, mask3))
        self.assertTrue(fm.data.tools.is_sub_mask(np.ma.nomask, mask1))
        self.assertTrue(fm.data.tools.is_sub_mask(np.ma.nomask, mask2))
        self.assertTrue(fm.data.tools.is_sub_mask(np.ma.nomask, mask3))
        self.assertTrue(fm.data.tools.is_sub_mask(np.ma.nomask, mask4))
        self.assertTrue(fm.data.tools.is_sub_mask(np.ma.nomask, mask5))
        self.assertTrue(fm.data.tools.is_sub_mask(np.ma.nomask, np.ma.nomask))
        self.assertTrue(fm.data.tools.is_sub_mask(mask5, np.ma.nomask))
        self.assertFalse(fm.data.tools.is_sub_mask(mask1, mask6))
        self.assertFalse(fm.data.tools.is_sub_mask(mask1, mask7))

        # equal mask
        self.assertTrue(fm.data.tools.masks_equal(None, None))
        self.assertTrue(fm.data.tools.masks_equal(fm.Mask.NONE, fm.Mask.NONE))
        self.assertTrue(fm.data.tools.masks_equal(fm.Mask.FLEX, fm.Mask.FLEX))
        self.assertFalse(fm.data.tools.masks_equal(fm.Mask.FLEX, fm.Mask.NONE))
        self.assertTrue(fm.data.tools.masks_equal(np.ma.nomask, np.ma.nomask))
        self.assertTrue(fm.data.tools.masks_equal(np.ma.nomask, mask5))
        self.assertTrue(fm.data.tools.masks_equal(mask5, np.ma.nomask))
        self.assertFalse(fm.data.tools.masks_equal(mask1, mask6, grid1, grid2))
        self.assertFalse(fm.data.tools.masks_equal(mask1, mask7, grid1, grid3))
        self.assertFalse(fm.data.tools.masks_equal(mask1, mask2, grid1, grid1))

        # cover domain
        self.assertTrue(fm.data.tools.check_data_covers_domain(data, mask3))
        self.assertFalse(fm.data.tools.check_data_covers_domain(data, mask2))
        self.assertFalse(fm.data.tools.check_data_covers_domain(data, np.ma.nomask))

        np.testing.assert_array_almost_equal(data, fm.data.tools.to_masked(data))
        np.testing.assert_array_almost_equal((1, 2, 3), fm.data.tools.filled((1, 2, 3)))

    def test_info_mask(self):
        grid = fm.RectilinearGrid([(1.0, 2.0, 3.0)])
        mask = np.array((1, 0, 0), dtype=bool)
        with self.assertRaises(fm.FinamMetaDataError):
            fm.Info(grid=grid, mask=mask)


if __name__ == "__main__":
    unittest.main()
