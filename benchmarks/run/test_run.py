import datetime as dt
import unittest

import pytest

import finam as fm


class SimpleRunBase(unittest.TestCase):
    def setup(self, benchmark):
        self.benchmark = benchmark
        self.start_time = dt.datetime(2000, 1, 1)
        self.end_time = dt.datetime(2000, 12, 31)
        self.counter = 0

    def gen_data(self, t):
        d = self.data[self.counter % 2]
        self.counter += 1
        return d

    def run_simulation(self):
        source = fm.modules.CallbackGenerator(
            callbacks={"Out": (self.gen_data, self.info1.copy())},
            start=self.start_time,
            step=dt.timedelta(days=1),
        )
        sink = fm.modules.DebugConsumer(
            inputs={
                "In": self.info2.copy(),
            },
            start=self.start_time,
            step=dt.timedelta(days=1),
        )

        self.composition = fm.Composition([source, sink])
        self.composition.initialize()

        source["Out"] >> sink["In"]

        self.composition.run(end_time=self.end_time)

    def run_test(self, sx, sy):
        self.setup_data(size=(sx, sy))
        self.benchmark(self.run_simulation)


class TestSimpleRun(SimpleRunBase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.setup(benchmark)

    def setup_data(self, size):
        self.info1 = fm.Info(time=None, grid=fm.UniformGrid(size), units="m")
        self.info2 = fm.Info(time=None, grid=fm.UniformGrid(size), units="m")
        self.data = [
            fm.data.full(0.0, "input", self.info1),
            fm.data.full(0.0, "input", self.info1),
        ]

    @pytest.mark.benchmark(group="run-sim")
    def test_run_simple_01_2x1(self):
        self.run_test(2, 1)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_simple_02_32x16(self):
        self.run_test(32, 16)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_simple_03_64x32(self):
        self.run_test(64, 32)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_simple_04_128x64(self):
        self.run_test(128, 64)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_simple_05_256x128(self):
        self.run_test(256, 128)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_simple_06_512x256(self):
        self.run_test(512, 256)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_simple_07_1024x512(self):
        self.run_test(1024, 512)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_simple_08_2048x1024(self):
        self.run_test(2048, 1024)


class TestSimpleRunUnits(SimpleRunBase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.setup(benchmark)

    def setup_data(self, size):
        self.info1 = fm.Info(time=None, grid=fm.UniformGrid(size), units="m")
        self.info2 = fm.Info(time=None, grid=fm.UniformGrid(size), units="km")
        self.data = [
            fm.data.full(0.0, "input", self.info1),
            fm.data.full(0.0, "input", self.info1),
        ]

    @pytest.mark.benchmark(group="run-sim")
    def test_run_units_01_2x1(self):
        self.run_test(2, 1)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_units_02_32x16(self):
        self.run_test(32, 16)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_units_03_64x32(self):
        self.run_test(64, 32)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_units_04_128x64(self):
        self.run_test(128, 64)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_units_05_256x128(self):
        self.run_test(256, 128)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_units_06_512x256(self):
        self.run_test(512, 256)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_units_07_1024x512(self):
        self.run_test(1024, 512)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_units_08_2048x1024(self):
        self.run_test(2048, 1024)


class TestSimpleRunNumpy(SimpleRunBase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.setup(benchmark)

    def setup_data(self, size):
        self.info1 = fm.Info(time=None, grid=fm.UniformGrid(size), units="m")
        self.info2 = fm.Info(time=None, grid=fm.UniformGrid(size), units="m")
        self.data = [
            fm.data.strip_data(fm.data.full(0.0, "input", self.info1)),
            fm.data.strip_data(fm.data.full(0.0, "input", self.info1)),
        ]

    @pytest.mark.benchmark(group="run-sim")
    def test_run_numpy_01_2x1(self):
        self.run_test(2, 1)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_numpy_02_32x16(self):
        self.run_test(32, 16)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_numpy_03_64x32(self):
        self.run_test(64, 32)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_numpy_04_128x64(self):
        self.run_test(128, 64)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_numpy_05_256x128(self):
        self.run_test(256, 128)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_numpy_06_512x256(self):
        self.run_test(512, 256)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_numpy_07_1024x512(self):
        self.run_test(1024, 512)

    @pytest.mark.benchmark(group="run-sim")
    def test_run_numpy_08_2048x1024(self):
        self.run_test(2048, 1024)
