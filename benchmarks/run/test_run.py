import datetime as dt
import unittest

import pytest

import finam as fm


class TestSimpleRun(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark
        self.start_time = dt.datetime(2000, 1, 1)
        self.end_time = dt.datetime(2000, 12, 31)

    def gen_data(self, t):
        d = self.data.copy()
        d = fm.data.assign_time(d, t)
        return d

    def setup_data(self, size):
        self.info = fm.Info(time=None, grid=fm.UniformGrid(size), units="m")
        self.data = fm.data.full(0.0, "input", self.info, self.start_time)

    def run_simulation(self):
        source = fm.modules.CallbackGenerator(
            callbacks={"Out": (self.gen_data, self.info.copy())},
            start=self.start_time,
            step=dt.timedelta(days=1),
        )
        sink = fm.modules.DebugConsumer(
            inputs={
                "In": self.info.copy(),
            },
            start=self.start_time,
            step=dt.timedelta(days=1),
        )

        self.composition = fm.Composition([source, sink])
        self.composition.initialize()

        source["Out"] >> sink["In"]

        self.composition.run(end_time=self.end_time)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_01_2x1(self):
        self.setup_data(size=(2, 1))
        self.benchmark(self.run_simulation)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_02_32x16(self):
        self.setup_data(size=(32, 16))
        self.benchmark(self.run_simulation)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_03_64x32(self):
        self.setup_data(size=(64, 32))
        self.benchmark(self.run_simulation)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_04_128x64(self):
        self.setup_data(size=(128, 64))
        self.benchmark(self.run_simulation)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_05_256x128(self):
        self.setup_data(size=(256, 128))
        self.benchmark(self.run_simulation)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_06_512x256(self):
        self.setup_data(size=(512, 256))
        self.benchmark(self.run_simulation)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_07_1024x512(self):
        self.setup_data(size=(1024, 512))
        self.benchmark(self.run_simulation)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_08_2048x1024(self):
        self.setup_data(size=(2048, 1024))
        self.benchmark(self.run_simulation)
