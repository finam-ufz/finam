import datetime as dt
import unittest

import numpy as np
import pytest

import finam as fm
from finam.data.tools import (
    check,
    compatible_units,
    equivalent_units,
    full,
    full_like,
    get_magnitude,
    get_units,
    is_quantified,
    prepare,
    strip_time,
    to_units,
)


class TestCheck(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    @pytest.mark.benchmark(group="data-tools")
    def test_check_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(check, xdata=xdata, info=info)

    @pytest.mark.benchmark(group="data-tools")
    def test_check_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(check, xdata=xdata, info=info)


class TestPrepare(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    def copy_numpy_prepare(self, data, info):
        return prepare(np.copy(data), info=info)

    @pytest.mark.benchmark(group="data-tools")
    def test_prepare_np_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(prepare, data=xdata, info=info)

    @pytest.mark.benchmark(group="data-tools")
    def test_prepare_np_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(prepare, data=xdata, info=info)

    @pytest.mark.benchmark(group="data-tools")
    def test_prepare_np_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(prepare, data=xdata, info=info)

    @pytest.mark.benchmark(group="data-tools")
    def test_prepare_np_units_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, info).magnitude
        _result = self.benchmark(prepare, data=xdata, info=info)

    @pytest.mark.benchmark(group="data-tools")
    def test_prepare_np_units_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, info).magnitude
        _result = self.benchmark(prepare, data=xdata, info=info)

    @pytest.mark.benchmark(group="data-tools")
    def test_prepare_np_units_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, info).magnitude
        _result = self.benchmark(prepare, data=xdata, info=info)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_cp_prepare_np_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(self.copy_numpy_prepare, data=xdata, info=info)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_cp_prepare_np_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(self.copy_numpy_prepare, data=xdata, info=info)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_cp_prepare_np_03_1024x512(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((1024, 512)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(self.copy_numpy_prepare, data=xdata, info=info)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_cp_prepare_np_04_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(self.copy_numpy_prepare, data=xdata, info=info)


class TestFull(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_full_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        _result = self.benchmark(full, value=0.0, info=info)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_full_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        _result = self.benchmark(full, value=0.0, info=info)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_full_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        _result = self.benchmark(full, value=0.0, info=info)


class TestFullLike(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_full_like_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(full_like, xdata=xdata, value=0.0)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_full_like_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(full_like, xdata=xdata, value=0.0)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_full_like_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(full_like, xdata=xdata, value=0.0)


class TestTimeTools(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    @pytest.mark.benchmark(group="data-tools")
    def test_strip_time(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(strip_time, xdata=xdata, grid=info.grid)


class TestUnitsTools(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    @pytest.mark.benchmark(group="data-tools")
    def test_get_units(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(get_units, xdata=xdata)

    @pytest.mark.benchmark(group="data-tools")
    def test_is_quantified(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(is_quantified, xdata=xdata)

    @pytest.mark.benchmark(group="data-tools")
    def test_equivalent_units_true(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="mm")
        xdata = full(0.0, info)
        result = self.benchmark(equivalent_units, unit1=xdata, unit2="L/m^2")
        self.assertTrue(result)

    @pytest.mark.benchmark(group="data-tools")
    def test_equivalent_units_false(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="mm")
        xdata = full(0.0, info)
        result = self.benchmark(equivalent_units, unit1=xdata, unit2="m")
        self.assertFalse(result)

    @pytest.mark.benchmark(group="data-tools")
    def test_compatible_units(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="mm")
        xdata = full(0.0, info)
        _result = self.benchmark(compatible_units, unit1=xdata, unit2="km")

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_to_units_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(to_units, xdata=xdata, units="in")

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_to_units_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(to_units, xdata=xdata, units="in")

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_to_units_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(to_units, xdata=xdata, units="in")

    @pytest.mark.benchmark(group="data-tools")
    def test_to_units_noop_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(to_units, xdata=xdata, units="m")

    @pytest.mark.benchmark(group="data-tools")
    def test_to_units_noop_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(to_units, xdata=xdata, units="m")

    @pytest.mark.benchmark(group="data-tools")
    def test_to_units_noop_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(to_units, xdata=xdata, units="m")

    @pytest.mark.benchmark(group="data-tools")
    def test_get_magnitude_01_2x1(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2, 1)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(get_magnitude, xdata=xdata)

    @pytest.mark.benchmark(group="data-tools")
    def test_get_magnitude_02_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(get_magnitude, xdata=xdata)

    @pytest.mark.benchmark(group="data-tools")
    def test_get_magnitude_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, info)
        _result = self.benchmark(get_magnitude, xdata=xdata)

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_set_units_mul_01_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, info).magnitude
        _result = self.benchmark(set_units_mul, data=xdata, units=fm.UNITS.Unit("m"))

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_set_units_mul_02_1024x512(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((1024, 512)), units="m")
        xdata = full(0.0, info).magnitude
        _result = self.benchmark(set_units_mul, data=xdata, units=fm.UNITS.Unit("m"))

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_set_units_mul_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, info).magnitude
        _result = self.benchmark(set_units_mul, data=xdata, units=fm.UNITS.Unit("m"))

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_set_units_quant_01_512x256(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((512, 256)), units="m")
        xdata = full(0.0, info).magnitude
        _result = self.benchmark(set_units_qua, data=xdata, units=fm.UNITS.Unit("m"))

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_set_units_quant_02_1024x512(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((1024, 512)), units="m")
        xdata = full(0.0, info).magnitude
        _result = self.benchmark(set_units_qua, data=xdata, units=fm.UNITS.Unit("m"))

    @pytest.mark.benchmark(group="data-tools-slow")
    def test_set_units_quant_03_2048x1024(self):
        time = dt.datetime(2000, 1, 1)
        info = fm.Info(time=time, grid=fm.UniformGrid((2048, 1024)), units="m")
        xdata = full(0.0, info).magnitude
        _result = self.benchmark(set_units_qua, data=xdata, units=fm.UNITS.Unit("m"))


def set_units_mul(data, units):
    return data * units


def set_units_qua(data, units):
    return fm.UNITS.Quantity(data, units)
