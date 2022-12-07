import datetime as dt
import tempfile
import unittest

import pytest

import finam as fm


class TestPushPullBase(unittest.TestCase):
    def push_pull(self):
        # Trick the shared memory check in the output
        data = self.data[self.counter % 2]

        self.out.push_data(data, self.time)
        data = self.inp.pull_data(self.time)
        self.time += dt.timedelta(days=1)
        self.counter += 1
        return data

    def setup_link(self, grid, target_units, memory_limit=None, tempdir=None):
        self.time = dt.datetime(2000, 1, 1)
        info1 = fm.Info(time=self.time, grid=grid, units="mm")
        info2 = fm.Info(time=self.time, grid=grid, units=target_units)

        self.data = [
            fm.data.full(0.0, info1),
            fm.data.full(0.0, info1),
        ]

        self.out = fm.Output(name="Output")
        self.inp = fm.Input(name="Input")

        self.out.memory_limit = memory_limit
        self.out.memory_location = tempdir

        self.out >> self.inp
        self.inp.ping()
        self.out.push_info(info1)
        self.inp.exchange_info(info2)


class TestPushPull(TestPushPullBase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark
        self.counter = 0

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_01_2x1(self):
        grid = fm.UniformGrid((2, 1))
        self.setup_link(grid, target_units="mm")
        data = self.benchmark(self.push_pull)
        self.assertEqual(fm.UNITS.millimeter, data.units)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_02_512x256(self):
        grid = fm.UniformGrid((512, 256))
        self.setup_link(grid, target_units="mm")
        data = self.benchmark(self.push_pull)
        self.assertEqual(fm.UNITS.millimeter, data.units)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_03_1024x512(self):
        grid = fm.UniformGrid((1024, 512))
        self.setup_link(grid, target_units="mm")
        data = self.benchmark(self.push_pull)
        self.assertEqual(fm.UNITS.millimeter, data.units)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_04_2048x1024(self):
        grid = fm.UniformGrid((2048, 1024))
        self.setup_link(grid, target_units="mm")
        data = self.benchmark(self.push_pull)
        self.assertEqual(fm.UNITS.millimeter, data.units)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_units_01_2x1(self):
        grid = fm.UniformGrid((2, 1))
        self.setup_link(grid, target_units="km")
        data = self.benchmark(self.push_pull)
        self.assertEqual(fm.UNITS.kilometer, data.units)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_units_02_512x256(self):
        grid = fm.UniformGrid((512, 256))
        self.setup_link(grid, target_units="km")
        data = self.benchmark(self.push_pull)
        self.assertEqual(fm.UNITS.kilometer, data.units)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_units_03_1024x512(self):
        grid = fm.UniformGrid((1024, 512))
        self.setup_link(grid, target_units="km")
        data = self.benchmark(self.push_pull)
        self.assertEqual(fm.UNITS.kilometer, data.units)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_units_04_2048x1024(self):
        grid = fm.UniformGrid((2048, 1024))
        self.setup_link(grid, target_units="km")
        data = self.benchmark(self.push_pull)
        self.assertEqual(fm.UNITS.kilometer, data.units)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_equiv_01_2x1(self):
        grid = fm.UniformGrid((2, 1))
        self.setup_link(grid, target_units="L/m^2")
        data = self.benchmark(self.push_pull)
        self.assertEqual(fm.UNITS.Unit("L/m^2"), data.units)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_equiv_02_512x256(self):
        grid = fm.UniformGrid((512, 256))
        self.setup_link(grid, target_units="L/m^2")
        data = self.benchmark(self.push_pull)
        self.assertEqual(fm.UNITS.Unit("L/m^2"), data.units)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_equiv_03_1024x512(self):
        grid = fm.UniformGrid((1024, 512))
        self.setup_link(grid, target_units="L/m^2")
        data = self.benchmark(self.push_pull)
        self.assertEqual(fm.UNITS.Unit("L/m^2"), data.units)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_equiv_04_2048x1024(self):
        grid = fm.UniformGrid((2048, 1024))
        self.setup_link(grid, target_units="L/m^2")
        data = self.benchmark(self.push_pull)
        self.assertEqual(fm.UNITS.Unit("L/m^2"), data.units)

    @pytest.mark.benchmark(group="sdk-io-mem")
    def test_push_pull_file_01_2x1(self):
        grid = fm.UniformGrid((2, 1))
        with tempfile.TemporaryDirectory() as td:
            self.setup_link(grid, target_units="m", memory_limit=0, tempdir=td)
            self.benchmark(self.push_pull)
            self.out.finalize()

    @pytest.mark.benchmark(group="sdk-io-mem")
    def test_push_pull_file_02_512x256(self):
        grid = fm.UniformGrid((512, 256))
        with tempfile.TemporaryDirectory() as td:
            self.setup_link(grid, target_units="m", memory_limit=0, tempdir=td)
            self.benchmark(self.push_pull)
            self.out.finalize()

    @pytest.mark.benchmark(group="sdk-io-mem")
    def test_push_pull_file_03_1024x512(self):
        grid = fm.UniformGrid((1024, 512))
        with tempfile.TemporaryDirectory() as td:
            self.setup_link(grid, target_units="m", memory_limit=0, tempdir=td)
            self.benchmark(self.push_pull)
            self.out.finalize()

    @pytest.mark.benchmark(group="sdk-io-mem")
    def test_push_pull_file_04_2048x1024(self):
        grid = fm.UniformGrid((2048, 1024))
        with tempfile.TemporaryDirectory() as td:
            self.setup_link(grid, target_units="m", memory_limit=0, tempdir=td)
            self.benchmark(self.push_pull)
            self.out.finalize()
