import unittest

import numpy as np
import pytest

import finam as fm


class TestCreateUniform(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    def create_grid(self, size):
        return fm.UniformGrid(size)

    @pytest.mark.benchmark(group="data-create-grids")
    def test_create_uniform_01_2x1(self):
        _result = self.benchmark(self.create_grid, size=(2, 1))

    @pytest.mark.benchmark(group="data-create-grids")
    def test_create_uniform_02_512x256(self):
        _result = self.benchmark(self.create_grid, size=(512, 256))

    @pytest.mark.benchmark(group="data-create-grids")
    def test_create_uniform_03_2048x1024(self):
        _result = self.benchmark(self.create_grid, size=(2048, 1024))


class TestCreateRectilinear(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    def create_grid(self, axes):
        return fm.RectilinearGrid(axes)

    @pytest.mark.benchmark(group="data-create-grids")
    def test_create_rectilinear_01_2x1(self):
        axes = [np.asarray(range(2)), np.asarray(range(1))]
        _result = self.benchmark(self.create_grid, axes=axes)

    @pytest.mark.benchmark(group="data-create-grids")
    def test_create_rectilinear_02_512x256(self):
        axes = [np.asarray(range(512)), np.asarray(range(256))]
        _result = self.benchmark(self.create_grid, axes=axes)

    @pytest.mark.benchmark(group="data-create-grids")
    def test_create_rectilinear_03_2048x1024(self):
        axes = [np.asarray(range(2048)), np.asarray(range(1024))]
        _result = self.benchmark(self.create_grid, axes=axes)


class TestGridFunctionsSimple(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    def get_cell_axes(self, grid):
        return grid.cell_axes

    @pytest.mark.benchmark(group="data-grid-functions")
    def test_cell_axes_01_2x1(self):
        grid = fm.UniformGrid((2, 1))
        _result = self.benchmark(self.get_cell_axes, grid=grid)

    @pytest.mark.benchmark(group="data-grid-functions")
    def test_cell_axes_02_512x256(self):
        grid = fm.UniformGrid((512, 256))
        _result = self.benchmark(self.get_cell_axes, grid=grid)

    @pytest.mark.benchmark(group="data-grid-functions")
    def test_cell_axes_03_2048x1024(self):
        grid = fm.UniformGrid((2048, 1024))
        _result = self.benchmark(self.get_cell_axes, grid=grid)


class TestGridFunctionsSlow(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setupBenchmark(self, benchmark):
        self.benchmark = benchmark

    def get_points(self, grid):
        return grid.points

    @pytest.mark.benchmark(group="data-grid-functions-slow")
    def test_points_01_2x1(self):
        grid = fm.UniformGrid((2, 1))
        _result = self.benchmark(self.get_points, grid=grid)

    @pytest.mark.benchmark(group="data-grid-functions-slow")
    def test_points_02_512x256(self):
        grid = fm.UniformGrid((512, 256))
        _result = self.benchmark(self.get_points, grid=grid)

    @pytest.mark.benchmark(group="data-grid-functions-slow")
    def test_points_03_2048x1024(self):
        grid = fm.UniformGrid((2048, 1024))
        _result = self.benchmark(self.get_points, grid=grid)

    def get_cell_centers(self, grid):
        return grid.cell_centers

    @pytest.mark.benchmark(group="data-grid-functions-slow")
    def test_cell_centers_01_2x1(self):
        grid = fm.UniformGrid((2, 1))
        _result = self.benchmark(self.get_cell_centers, grid=grid)

    @pytest.mark.benchmark(group="data-grid-functions-slow")
    def test_cell_centers_02_512x256(self):
        grid = fm.UniformGrid((512, 256))
        _result = self.benchmark(self.get_cell_centers, grid=grid)

    @pytest.mark.benchmark(group="data-grid-functions-slow")
    def test_cell_centers_03_2048x1024(self):
        grid = fm.UniformGrid((2048, 1024))
        _result = self.benchmark(self.get_cell_centers, grid=grid)

    def get_cells(self, grid):
        return grid.cells

    @pytest.mark.benchmark(group="data-grid-functions-slow")
    def test_cells_01_2x1(self):
        grid = fm.UniformGrid((2, 1))
        _result = self.benchmark(self.get_cells, grid=grid)

    @pytest.mark.benchmark(group="data-grid-functions-slow")
    def test_cells_02_512x256(self):
        grid = fm.UniformGrid((512, 256))
        _result = self.benchmark(self.get_cells, grid=grid)

    @pytest.mark.benchmark(group="data-grid-functions-slow")
    def test_cells_03_2048x1024(self):
        grid = fm.UniformGrid((2048, 1024))
        _result = self.benchmark(self.get_cells, grid=grid)
