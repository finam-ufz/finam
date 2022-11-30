import datetime as dt
import unittest

import pytest

import finam as fm
from finam.data.tools import (
    assign_time,
    check,
    compatible_units,
    equivalent_units,
    full,
    full_like,
    get_magnitude,
    get_time,
    get_units,
    has_time,
    is_quantified,
    strip_data,
    strip_time,
    to_units,
    to_xarray,
)


class TestCheckXarray(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    @pytest.mark.benchmark(group="data-tools")
    def test_check_xarray_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(check, xdata=xdata, name="test", info=info, time=time)

    @pytest.mark.benchmark(group="data-tools")
    def test_check_xarray_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(check, xdata=xdata, name="test", info=info, time=time)


class TestToXarray(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    @pytest.mark.benchmark(group="data-tools")
    def test_to_xarray_np_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        data = strip_data(xdata)
        _result = self.benchmark(
            to_xarray, data=data, name="test", info=info, time=time
        )

    @pytest.mark.benchmark(group="data-tools")
    def test_to_xarray_np_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, "test", info, time)
        data = strip_data(xdata)
        _result = self.benchmark(
            to_xarray, data=data, name="test", info=info, time=time
        )

    @pytest.mark.benchmark(group="data-tools")
    def test_to_xarray_np_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, "test", info, time)
        data = strip_data(xdata)
        _result = self.benchmark(
            to_xarray, data=data, name="test", info=info, time=time
        )

    @pytest.mark.benchmark(group="data-tools")
    def test_to_xarray_xr_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(
            to_xarray, data=xdata, name="test", info=info, time=time
        )

    @pytest.mark.benchmark(group="data-tools")
    def test_to_xarray_xr_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(
            to_xarray, data=xdata, name="test", info=info, time=time
        )

    @pytest.mark.benchmark(group="data-tools")
    def test_to_xarray_xr_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(
            to_xarray, data=xdata, name="test", info=info, time=time
        )


class TestFull(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_full_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        _result = self.benchmark(full, value=0.0, name="test", info=info, time=time)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_full_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        _result = self.benchmark(full, value=0.0, name="test", info=info, time=time)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_full_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        _result = self.benchmark(full, value=0.0, name="test", info=info, time=time)


class TestFullLike(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_full_like_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(full_like, xdata=xdata, value=0.0)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_full_like_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(full_like, xdata=xdata, value=0.0)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_full_like_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(full_like, xdata=xdata, value=0.0)


class TestTimeTools(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    @pytest.mark.benchmark(group="data-tools")
    def test_strip_time(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(strip_time, xdata=xdata)

    @pytest.mark.benchmark(group="data-tools")
    def test_assign_time_update(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(assign_time, xdata=xdata, time=dt.datetime(2000, 1, 2))

    @pytest.mark.benchmark(group="data-tools")
    def test_assign_time_add(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        xdata = strip_time(xdata)
        _result = self.benchmark(assign_time, xdata=xdata, time=dt.datetime(2000, 1, 2))

    @pytest.mark.benchmark(group="data-tools")
    def test_get_time(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(get_time, xdata=xdata)

    @pytest.mark.benchmark(group="data-tools")
    def test_get_time_neg(self):
        time = dt.datetime(1800, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(get_time, xdata=xdata)

    @pytest.mark.benchmark(group="data-tools")
    def test_has_time(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(has_time, xdata=xdata)


class TestUnitsTools(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    @pytest.mark.benchmark(group="data-tools")
    def test_get_units(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(get_units, xdata=xdata)

    @pytest.mark.benchmark(group="data-tools")
    def test_is_quantified(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(is_quantified, xdata=xdata)

    @pytest.mark.benchmark(group="data-tools")
    def test_equivalent_units_true(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="mm")
        xdata = full(0.0, "test", info, time)
        result = self.benchmark(equivalent_units, unit1=xdata, unit2="L/m^2")
        self.assertTrue(result)

    @pytest.mark.benchmark(group="data-tools")
    def test_equivalent_units_False(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="mm")
        xdata = full(0.0, "test", info, time)
        result = self.benchmark(equivalent_units, unit1=xdata, unit2="m")
        self.assertFalse(result)

    @pytest.mark.benchmark(group="data-tools")
    def test_compatible_units(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="mm")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(compatible_units, unit1=xdata, unit2="km")

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_to_units_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(to_units, xdata=xdata, units="in")

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_to_units_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(to_units, xdata=xdata, units="in")

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_to_units_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(to_units, xdata=xdata, units="in")

    @pytest.mark.benchmark(group="data-tools")
    def test_to_units_noop_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(to_units, xdata=xdata, units="m")

    @pytest.mark.benchmark(group="data-tools")
    def test_to_units_noop_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(to_units, xdata=xdata, units="m")

    @pytest.mark.benchmark(group="data-tools")
    def test_to_units_noop_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(to_units, xdata=xdata, units="m")

    @pytest.mark.benchmark(group="data-tools")
    def test_get_magnitude_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(get_magnitude, xdata=xdata)

    @pytest.mark.benchmark(group="data-tools")
    def test_get_magnitude_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(get_magnitude, xdata=xdata)

    @pytest.mark.benchmark(group="data-tools")
    def test_get_magnitude_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, "test", info, time)
        _result = self.benchmark(get_magnitude, xdata=xdata)
