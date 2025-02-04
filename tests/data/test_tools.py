import datetime
import unittest
from datetime import datetime as dt

import numpy as np
import pint

import finam
import finam.errors


class TestDataTools(unittest.TestCase):
    def test_check(self):
        time = dt(2000, 1, 1)

        grid = finam.EsriGrid(2, 3)
        gri0 = finam.EsriGrid(2, 3, axes_names=["lat", "lon"])
        gri1 = finam.EsriGrid(3, 2)

        info = finam.Info(time, grid, units="m", foo="bar")
        inf0 = info.copy_with(units="meter")
        inf1 = info.copy_with(foo="spam")
        inf2 = info.copy_with(units="s")
        inf3 = info.copy_with(grid=gri0)
        inf4 = info.copy_with(grid=gri1)

        time = dt(year=2022, month=10, day=12)
        tim0 = dt(year=2021, month=10, day=12)

        data = np.arange(6).reshape(3, 2)
        dar0 = finam.data.prepare(data, info)
        dar1 = finam.data.prepare(data, info)

        # assert stuff
        self.assertIsInstance(finam.data.get_magnitude(dar0), np.ndarray)
        self.assertIsInstance(finam.data.strip_time(dar0, info.grid), pint.Quantity)
        self.assertIsInstance(
            finam.data.get_dimensionality(dar0), pint.util.UnitsContainer
        )

        # should work
        finam.data.prepare(dar0, info)
        finam.data.prepare(dar1, info)
        finam.data.check(dar0, info)
        finam.data.check(dar1, info)
        finam.data.to_units(dar0, "km")

        # wrong shape
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.prepare(1, info)

        # no DataArray
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(None, info)

        # not qunatified
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(dar0.magnitude, info)

        finam.data.check(dar1, inf0)

        # other units format should work
        finam.data.check(dar0, inf0)

        # wrong units
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(dar0, inf2)

        # wrong shape
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(dar0, inf4)
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(dar1, inf4)

        # check full_like
        dar2 = finam.data.full_like(dar0, 0)
        finam.data.check(dar2, info)

        dar3 = finam.data.full(0, info)
        finam.data.check(dar3, info)

    def test_other_grids(self):
        time = dt(2000, 1, 1)

        gri0 = finam.NoGrid(dim=1)
        gri1 = finam.UnstructuredPoints(points=[[0, 0], [0, 2], [2, 2]])
        info = finam.Info(time, gri0, units="s")
        data = np.arange(3)
        dar0 = finam.data.prepare(data, info)
        dar1 = finam.data.prepare(data, info.copy_with(grid=gri1))

        self.assertEqual((1, 3), dar0.shape)
        self.assertEqual((1, 3), dar1.shape)

    def test_strip_time(self):
        time = dt(2000, 1, 1)
        grid = finam.NoGrid()

        xdata = finam.data.prepare(1.0, finam.Info(time, grid=grid))
        self.assertEqual(xdata.shape, (1,))
        stripped = finam.data.strip_time(xdata, grid)
        self.assertEqual(stripped.shape, ())

        xdata = finam.data.prepare(
            [1.0, 2.0, 3.0],
            finam.Info(time, grid=finam.NoGrid(dim=1)),
        )
        self.assertEqual(xdata.shape, (1, 3))
        stripped = finam.data.strip_time(xdata, finam.NoGrid(dim=1))
        self.assertEqual(stripped.shape, (3,))
        stripped2 = finam.data.strip_time(xdata, finam.NoGrid(dim=1))
        self.assertEqual(stripped2.shape, stripped.shape)

        arr1 = finam.data.prepare(
            1.0,
            finam.Info(time, grid=finam.NoGrid()),
        )
        arr2 = finam.data.prepare(
            1.0,
            finam.Info(time, grid=finam.NoGrid()),
        )
        data = np.concatenate([arr1, arr2], axis=0)
        with self.assertRaises(finam.errors.FinamDataError):
            stripped_ = finam.data.strip_time(data, finam.NoGrid())

    def test_prepare(self):
        time = dt(2000, 1, 1)

        data = finam.data.prepare(1.0, finam.Info(time, grid=finam.NoGrid()))
        self.assertEqual(np.asarray([1.0]) * finam.UNITS(""), data)

        data = finam.data.prepare(
            [[1.0, 1.0], [1.0, 1.0]], finam.Info(time, grid=finam.UniformGrid((3, 3)))
        )
        self.assertEqual((1, 2, 2), data.shape)

        data = finam.data.prepare(
            finam.UNITS.Quantity(1.0, "m"),
            finam.Info(time, grid=finam.NoGrid(), units="m"),
        )

        self.assertEqual((1,), data.shape)
        self.assertEqual(finam.UNITS.meter, data.units)

        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.prepare(
                np.asarray([1, 2]), finam.Info(time, grid=finam.NoGrid())
            )

        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.prepare(
                1.0 * finam.UNITS.meter, finam.Info(time, grid=finam.NoGrid())
            )

        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.prepare(
                1.0 * finam.UNITS.meter,
                finam.Info(time, grid=finam.NoGrid(), units="m^3"),
            )

    def test_prepare_copy(self):
        time = dt(2000, 1, 1)
        info_1 = finam.Info(time, grid=finam.NoGrid(1), units="m")
        info_2 = finam.Info(time, grid=finam.NoGrid(1), units="km")

        # using numpy arrays without units
        data = np.asarray([1, 2])
        xdata = finam.data.prepare(data, info_1, force_copy=True)
        data[0] = 0
        self.assertNotEqual(xdata[0, 0], data[0])

        # using numpy arrays with units
        data = np.asarray([1, 2]) * finam.UNITS("m")
        xdata = finam.data.prepare(data, info_1)
        data[0] = 0 * finam.UNITS("m")
        self.assertEqual(xdata[0, 0], data[0])

        data = np.asarray([1, 2]) * finam.UNITS("m")
        xdata = finam.data.prepare(data, info_1, force_copy=True)
        data[0] = 0 * finam.UNITS("m")
        self.assertNotEqual(xdata[0, 0], data[0])

        data = np.asarray([1, 2]) * finam.UNITS("m")
        xdata = finam.data.prepare(data, info_2)
        data[0] = 0 * finam.UNITS("m")
        self.assertNotEqual(finam.data.get_magnitude(xdata[0, 0]), 0.0)

        xdata = finam.data.prepare(np.asarray([1, 2]), info_1)
        xdata2 = finam.data.prepare(xdata, info_1)
        xdata[0, 0] = 0 * finam.UNITS("m")
        self.assertEqual(xdata2[0, 0], xdata[0, 0])

        xdata = finam.data.prepare(np.asarray([1, 2]), info_1)
        xdata2 = finam.data.prepare(xdata, info_1, force_copy=True)
        xdata[0, 0] = 0 * finam.UNITS("m")
        self.assertNotEqual(xdata2[0, 0], xdata[0, 0])

        xdata = finam.data.prepare(np.asarray([1, 2]), info_1)
        xdata2 = finam.data.prepare(xdata, info_2)
        xdata[0, 0] = 0 * finam.UNITS("m")
        self.assertNotEqual(finam.data.get_magnitude(xdata2[0, 0]), 0.0)

        data = [1.0]
        xdata2 = finam.data.prepare(data, info_1, force_copy=True)
        self.assertEqual(1.0 * finam.UNITS.meter, xdata2[0])

        xdata2[0, 0] = 0 * finam.UNITS("m")
        self.assertNotEqual(0.0, data[0])

    def test_prepare_masked(self):
        time = dt(2000, 1, 1)

        info = finam.Info(
            time,
            grid=finam.UniformGrid((3, 4), data_location=finam.Location.POINTS),
            units="",
        )

        in_data = np.ma.MaskedArray(np.ndarray((3, 4)), mask=False)
        in_data.mask[0, 0] = True

        xdata = finam.data.prepare(in_data, info, force_copy=True)
        self.assertTrue(finam.data.is_masked_array(xdata))
        self.assertTrue(xdata.mask[0, 0, 0])
        self.assertFalse(xdata.mask[0, 1, 0])

        in_data = finam.data.quantify(in_data)
        xdata = finam.data.prepare(in_data, info, force_copy=True)
        self.assertTrue(finam.data.is_masked_array(xdata))
        self.assertTrue(xdata.mask[0, 0, 0])
        self.assertFalse(xdata.mask[0, 1, 0])

    def test_assert_type(self):
        finam.data.assert_type(self, "A", 1, [int, float])

        with self.assertRaises(TypeError):
            finam.data.assert_type(self, "A", "1", [int, float])

    def test_info(self):
        time = dt(2000, 1, 1)
        _info = finam.Info(time, grid=finam.NoGrid())

        with self.assertRaises(finam.errors.FinamMetaDataError):
            _info = finam.Info(time=1, grid=finam.NoGrid())

        with self.assertRaises(finam.errors.FinamMetaDataError):
            _info = finam.Info(time, grid=finam.NoGrid)

        info = finam.Info(time, grid=finam.NoGrid(), units="m", foo="bar")
        self.assertEqual(info, info.copy_with())

        self.assertFalse(info.accepts(0, {}))
        self.assertFalse(info.accepts(finam.Info(time=None, grid=None), {}))

        self.assertTrue(
            info.accepts(finam.Info(time, grid=finam.NoGrid(), units="m"), {})
        )
        self.assertTrue(
            info.accepts(finam.Info(time, grid=finam.NoGrid(), units="km"), {})
        )
        self.assertFalse(
            info.accepts(finam.Info(time, grid=finam.NoGrid(), units="s"), {})
        )

        self.assertTrue(
            info.accepts(
                finam.Info(time, grid=finam.NoGrid(), units="m", foo="baz"), {}
            )
        )

        self.assertEqual(info, info.copy())
        self.assertNotEqual(info, 0)

        with self.assertRaises(AttributeError):
            info.__getattr__("bar")

        info.__setattr__("bar", "baz")
        self.assertEqual(info.bar, "baz")

    def test_check_shape(self):
        time = dt(2000, 1, 1)
        xdata = finam.data.prepare(
            1.0,
            finam.Info(time, grid=finam.NoGrid()),
        )

        finam.data.tools.core._check_shape(xdata.shape[1:], finam.NoGrid())

        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.tools.core._check_shape(xdata.shape[1:], finam.NoGrid(dim=1))

    def test_quantify(self):
        xdata = np.asarray([1.0])
        xdata = finam.data.quantify(xdata, "m")
        self.assertEqual(finam.data.get_units(xdata), finam.UNITS.meter)

        xdata = np.asarray([1.0])
        xdata = finam.data.quantify(xdata)
        self.assertEqual(finam.data.get_units(xdata), finam.UNITS.dimensionless)

        xdata = np.asarray([1.0]) * finam.UNITS("")
        with self.assertRaises(finam.FinamDataError):
            xdata = finam.data.quantify(xdata)

    def test_to_datetime(self):
        t = np.datetime64("1900-01-01")
        self.assertEqual(datetime.datetime(1900, 1, 1), finam.data.to_datetime(t))

        t = np.datetime64("2000-01-01")
        self.assertEqual(datetime.datetime(2000, 1, 1), finam.data.to_datetime(t))

    def test_cache_units(self):
        finam.data.tools.clear_units_cache()

        self.assertEqual({}, finam.data.tools.units._UNIT_PAIRS_CACHE)

        eqiv = finam.data.tools.equivalent_units("mm", "L/m^2")
        self.assertTrue(eqiv)
        self.assertEqual(
            {(finam.UNITS.Unit("mm"), finam.UNITS.Unit("L/m^2")): (True, True)},
            finam.data.tools.units._UNIT_PAIRS_CACHE,
        )

        finam.data.tools.clear_units_cache()

        self.assertEqual({}, finam.data.tools.units._UNIT_PAIRS_CACHE)


if __name__ == "__main__":
    unittest.main()
