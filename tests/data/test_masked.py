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

        source = fm.modules.generators.CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: gen_masked(t.toordinal(), in_info.grid.data_shape),
                    in_info,
                )
            },
            start=time,
            step=timedelta(days=1),
        )

        sink = fm.modules.debug.DebugConsumer(
            {"Input": fm.Info(None, grid=None, units=None)},
            start=time,
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, sink])
        composition.initialize()
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


if __name__ == "__main__":
    unittest.main()
