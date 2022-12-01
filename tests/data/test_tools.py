import datetime
import unittest
from datetime import datetime as dt

import numpy as np
import pint
import xarray as xr

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
        dar0 = finam.data.to_xarray(data, "data", info)
        dar1 = finam.data.to_xarray(data, "data", info)

        # assert stuff
        self.assertIsInstance(finam.data.get_magnitude(dar0), np.ndarray)
        self.assertIsInstance(finam.data.get_data(dar0), pint.Quantity)
        self.assertIsInstance(
            finam.data.get_dimensionality(dar0), pint.util.UnitsContainer
        )

        # should work
        finam.data.to_xarray(dar0, "data", info, time)
        finam.data.to_xarray(dar1, "data", info)
        finam.data.check(dar0, "data", info)
        finam.data.check(dar1, "data", info)
        finam.data.to_units(dar0, "km")

        # wrong shape
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.to_xarray(1, "data", info)

        # no DataArray
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(None, "data", info)

        # not qunatified
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(dar0.pint.dequantify(), "data", info)

        # wrong name
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(dar0, "wrong", info)

        finam.data.check(dar1, "data", inf0)

        # other units format should work
        finam.data.check(dar0, "data", inf0)

        # wrong meta
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(dar0, "data", inf1)

        # wrong units
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(dar0, "data", inf2)

        # wrong dims
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(dar0, "data", inf3)

        # wrong shape
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(dar0, "data", inf4)
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.check(dar1, "data", inf4)

        # check full_like
        dar2 = finam.data.full_like(dar0, 0)
        finam.data.check(dar2, "data", info)

        dar3 = finam.data.full(0, "data", info)
        finam.data.check(dar3, "data", info)

    def test_other_grids(self):
        time = dt(2000, 1, 1)

        gri0 = finam.NoGrid(dim=1)
        gri1 = finam.UnstructuredPoints(points=[[0, 0], [0, 2], [2, 2]])
        info = finam.Info(time, gri0, units="s")
        data = np.arange(3)
        dar0 = finam.data.to_xarray(data, "data", info)
        dar1 = finam.data.to_xarray(data, "data", info.copy_with(grid=gri1))

        self.assertTrue("dim_0" in dar0.dims)
        self.assertTrue("id" in dar1.dims)

    def test_strip_time(self):
        time = dt(2000, 1, 1)

        xdata = finam.data.to_xarray(1.0, "data", finam.Info(time, grid=finam.NoGrid()))
        self.assertEqual(xdata.shape, (1,))
        stripped = finam.data.strip_time(xdata)
        self.assertEqual(stripped.shape, ())

        xdata = finam.data.to_xarray(
            1.0,
            "data",
            finam.Info(time, grid=finam.NoGrid()),
        )
        self.assertEqual(xdata.shape, (1,))
        stripped = finam.data.strip_time(xdata)
        self.assertEqual(stripped.shape, ())

        xdata = finam.data.to_xarray(
            [1.0, 2.0, 3.0],
            "data",
            finam.Info(time, grid=finam.NoGrid(dim=1)),
        )
        self.assertEqual(xdata.shape, (1, 3))
        stripped = finam.data.strip_time(xdata)
        self.assertEqual(stripped.shape, (3,))
        stripped2 = finam.data.strip_time(xdata)
        self.assertEqual(stripped2.shape, stripped.shape)

        with self.assertRaises(finam.errors.FinamDataError):
            stripped_ = finam.data.strip_time(np.asarray([1.0, 2.0]))

        arr1 = finam.data.to_xarray(
            1.0,
            "A",
            finam.Info(time, grid=finam.NoGrid()),
        )
        arr2 = finam.data.to_xarray(
            1.0,
            "A",
            finam.Info(time, grid=finam.NoGrid()),
        )
        data = xr.concat([arr1, arr2], dim="time")
        with self.assertRaises(finam.errors.FinamDataError):
            stripped_ = finam.data.strip_time(data)

    def test_strip_data(self):
        time = dt(2000, 1, 1)
        xdata = finam.data.to_xarray(1.0, "data", finam.Info(time, grid=finam.NoGrid()))
        self.assertEqual(xdata.shape, (1,))
        stripped = finam.data.strip_data(xdata)
        self.assertEqual(stripped.shape, ())
        self.assertTrue(isinstance(stripped, pint.Quantity))
        self.assertFalse(isinstance(stripped, xr.DataArray))

    def test_to_xarray(self):
        time = dt(2000, 1, 1)
        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.to_xarray(
                np.asarray([1, 2]), "A", finam.Info(time, grid=finam.NoGrid())
            )

        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.to_xarray(
                1.0 * finam.UNITS.meter, "A", finam.Info(time, grid=finam.NoGrid())
            )

        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.to_xarray(
                1.0 * finam.UNITS.meter,
                "A",
                finam.Info(time, grid=finam.NoGrid(), units="m^3"),
            )

    def test_to_xarray_copy(self):
        time = dt(2000, 1, 1)
        info_1 = finam.Info(time, grid=finam.NoGrid(1), units="m")
        info_2 = finam.Info(time, grid=finam.NoGrid(1), units="km")

        # using numpy arrays without units
        data = np.asarray([1, 2])
        xdata = finam.data.to_xarray(data, "test", info_1, force_copy=True)
        data[0] = 0
        self.assertNotEqual(xdata[0, 0], data[0])

        # using numpy arrays with units
        data = np.asarray([1, 2]) * finam.UNITS("m")
        xdata = finam.data.to_xarray(data, "test", info_1)
        data[0] = 0 * finam.UNITS("m")
        self.assertEqual(xdata[0, 0], data[0])

        data = np.asarray([1, 2]) * finam.UNITS("m")
        xdata = finam.data.to_xarray(data, "test", info_1, force_copy=True)
        data[0] = 0 * finam.UNITS("m")
        self.assertNotEqual(xdata[0, 0], data[0])

        data = np.asarray([1, 2]) * finam.UNITS("m")
        xdata = finam.data.to_xarray(data, "test", info_2)
        data[0] = 0 * finam.UNITS("m")
        self.assertNotEqual(finam.data.get_magnitude(xdata[0, 0]), 0.0)

        # using xarray arrays
        xdata = finam.data.to_xarray(np.asarray([1, 2]), "test", info_1)
        xdata2 = finam.data.to_xarray(xdata, "test", info_1)
        xdata[0, 0] = 0 * finam.UNITS("m")
        self.assertEqual(xdata2[0, 0], xdata[0, 0])

        xdata = finam.data.to_xarray(np.asarray([1, 2]), "test", info_1)
        xdata2 = finam.data.to_xarray(xdata, "test", info_1, force_copy=True)
        xdata[0, 0] = 0 * finam.UNITS("m")
        self.assertNotEqual(xdata2[0, 0], xdata[0, 0])

        xdata = finam.data.to_xarray(np.asarray([1, 2]), "test", info_1)
        xdata2 = finam.data.to_xarray(xdata, "test", info_2)
        xdata[0, 0] = 0 * finam.UNITS("m")
        self.assertNotEqual(finam.data.get_magnitude(xdata2[0, 0]), 0.0)

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

        self.assertFalse(
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
        xdata = finam.data.to_xarray(
            1.0,
            "data",
            finam.Info(time, grid=finam.NoGrid()),
        )

        finam.data.tools._check_shape(xdata, finam.NoGrid())

        with self.assertRaises(finam.errors.FinamDataError):
            finam.data.tools._check_shape(xdata, finam.NoGrid(dim=1))

    def test_quantify(self):
        xdata = xr.DataArray(1.0, attrs={"units": "m"})
        xdata = finam.data.quantify(xdata)
        self.assertEqual(finam.data.get_units(xdata), finam.UNITS.meter)

        xdata = xr.DataArray(1.0)
        xdata = finam.data.quantify(xdata)
        self.assertEqual(finam.data.get_units(xdata), finam.UNITS.dimensionless)
