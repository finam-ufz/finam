import datetime as dt
import unittest

import pytest

import finam as fm


class TestPushPull(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    def push_pull(self):
        self.out.push_data(self.data, self.time)
        _ = self.inp.pull_data(self.time)
        self.time += dt.timedelta(days=1)

    def setup_link(self, grid, target_units):
        self.time = dt.datetime(2000, 1, 1)
        info1 = fm.Info(time=self.time, grid=grid, units="m")
        info2 = fm.Info(time=self.time, grid=grid, units=target_units)
        self.data = fm.data.strip_data(fm.data.full(0.0, "test", info1, self.time))

        self.out = fm.Output(name="Output")
        self.inp = fm.Input(name="Input")

        self.out >> self.inp
        self.inp.ping()
        self.out.push_info(info1)
        self.inp.exchange_info(info2)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_01_2x1(self):
        grid = fm.UniformGrid((2, 1))
        self.setup_link(grid, target_units="m")
        self.benchmark(self.push_pull)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_02_512x256(self):
        grid = fm.UniformGrid((512, 256))
        self.setup_link(grid, target_units="m")
        self.benchmark(self.push_pull)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_03_2048x1024(self):
        grid = fm.UniformGrid((2048, 1024))
        self.setup_link(grid, target_units="m")
        self.benchmark(self.push_pull)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_units_01_2x1(self):
        grid = fm.UniformGrid((2, 1))
        self.setup_link(grid, target_units="km")
        self.benchmark(self.push_pull)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_units_02_512x256(self):
        grid = fm.UniformGrid((512, 256))
        self.setup_link(grid, target_units="km")
        self.benchmark(self.push_pull)

    @pytest.mark.benchmark(group="sdk-io")
    def test_push_pull_np_units_03_2048x1024(self):
        grid = fm.UniformGrid((2048, 1024))
        self.setup_link(grid, target_units="km")
        self.benchmark(self.push_pull)
