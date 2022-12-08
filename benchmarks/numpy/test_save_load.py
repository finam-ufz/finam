import os.path
import tempfile
import unittest

import numpy as np
import pytest

import finam as fm


class TestCreateUniform(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    @pytest.mark.benchmark(group="np-save-load")
    def test_save_01_64x32(self):
        xdata = np.full((1, 64, 32), 1.0, dtype=np.dtype(np.float64))
        with tempfile.TemporaryDirectory() as d:
            fp = os.path.join(d, "temp.npy")
            _result = self.benchmark(np.save, file=fp, arr=xdata)

    @pytest.mark.benchmark(group="np-save-load")
    def test_save_02_512x256(self):
        xdata = np.full((1, 512, 256), 1.0, dtype=np.dtype(np.float64))
        with tempfile.TemporaryDirectory() as d:
            fp = os.path.join(d, "temp.npy")
            _result = self.benchmark(np.save, file=fp, arr=xdata)

    @pytest.mark.benchmark(group="np-save-load")
    def test_save_03_1024x512(self):
        xdata = np.full((1, 1024, 512), 1.0, dtype=np.dtype(np.float64))
        with tempfile.TemporaryDirectory() as d:
            fp = os.path.join(d, "temp.npy")
            _result = self.benchmark(np.save, file=fp, arr=xdata)

    @pytest.mark.benchmark(group="np-save-load")
    def test_save_04_2048x1024(self):
        xdata = np.full((1, 2048, 1024), 1.0, dtype=np.dtype(np.float64))
        with tempfile.TemporaryDirectory() as d:
            fp = os.path.join(d, "temp.npy")
            _result = self.benchmark(np.save, file=fp, arr=xdata)

    @pytest.mark.benchmark(group="np-save-load")
    def test_load_01_64x32(self):
        xdata = np.full((1, 64, 32), 1.0, dtype=np.dtype(np.float64))
        with tempfile.TemporaryDirectory() as d:
            fp = os.path.join(d, "temp.npy")
            np.save(fp, xdata)
            _result = self.benchmark(np.load, file=fp)

    @pytest.mark.benchmark(group="np-save-load")
    def test_load_02_512x256(self):
        xdata = np.full((1, 512, 256), 1.0, dtype=np.dtype(np.float64))
        with tempfile.TemporaryDirectory() as d:
            fp = os.path.join(d, "temp.npy")
            np.save(fp, xdata)
            _result = self.benchmark(np.load, file=fp)

    @pytest.mark.benchmark(group="np-save-load")
    def test_load_03_1024x512(self):
        xdata = np.full((1, 1024, 512), 1.0, dtype=np.dtype(np.float64))
        with tempfile.TemporaryDirectory() as d:
            fp = os.path.join(d, "temp.npy")
            np.save(fp, xdata)
            _result = self.benchmark(np.load, file=fp)

    @pytest.mark.benchmark(group="np-save-load")
    def test_load_04_2048x1024(self):
        xdata = np.full((1, 2048, 1024), 1.0, dtype=np.dtype(np.float64))
        with tempfile.TemporaryDirectory() as d:
            fp = os.path.join(d, "temp.npy")
            np.save(fp, xdata)
            _result = self.benchmark(np.load, file=fp)
