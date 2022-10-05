import unittest

import numpy as np
from numpy.testing import assert_array_equal

from finam.data.grid_spec import RectilinearGrid, UniformGrid, UnstructuredGrid
from finam.data.grid_tools import CellType


class TestUniform(unittest.TestCase):
    def test_uniform(self):
        grid = UniformGrid((3, 2), spacing=(1.0, 2.0), origin=(2.0, 1.0))

        self.assertEqual(grid.dim, 2)
        self.assertEqual(grid.dims, (3, 2))
        self.assertEqual(grid.point_count, 6)
        self.assertEqual(grid.cell_count, 2)
        self.assertEqual(grid.data_shape, (2, 1))

        assert_array_equal(grid.axes[0], [2.0, 3.0, 4.0])
        assert_array_equal(grid.axes[1], [1.0, 3.0])

        assert_array_equal(grid.cell_axes[0], [2.5, 3.5])
        assert_array_equal(grid.cell_axes[1], [2.0])

        assert_array_equal(grid.data_axes[0], [2.5, 3.5])
        assert_array_equal(grid.data_axes[1], [2.0])

        assert_array_equal(
            grid.points,
            [[2.0, 1.0], [3.0, 1.0], [4.0, 1.0], [2.0, 3.0], [3.0, 3.0], [4.0, 3.0]],
        )
        assert_array_equal(grid.cells, [[3, 4, 1, 0], [4, 5, 2, 1]])
        assert_array_equal(grid.cell_centers, [[2.5, 2.0], [3.5, 2.0]])

        assert_array_equal(grid.cell_types, [CellType.QUAD.value, CellType.QUAD.value])

    def test_rectilinear(self):
        grid = RectilinearGrid([np.asarray([2.0, 3.0, 4.0]), np.asarray([1.0, 3.0])])

        self.assertEqual(grid.dim, 2)
        self.assertEqual(grid.dims, (3, 2))
        self.assertEqual(grid.point_count, 6)
        self.assertEqual(grid.cell_count, 2)
        self.assertEqual(grid.data_shape, (2, 1))

        assert_array_equal(grid.axes[0], [2.0, 3.0, 4.0])
        assert_array_equal(grid.axes[1], [1.0, 3.0])

        assert_array_equal(grid.cell_axes[0], [2.5, 3.5])
        assert_array_equal(grid.cell_axes[1], [2.0])

        assert_array_equal(grid.data_axes[0], [2.5, 3.5])
        assert_array_equal(grid.data_axes[1], [2.0])

        assert_array_equal(
            grid.points,
            [[2.0, 1.0], [3.0, 1.0], [4.0, 1.0], [2.0, 3.0], [3.0, 3.0], [4.0, 3.0]],
        )
        assert_array_equal(grid.cells, [[3, 4, 1, 0], [4, 5, 2, 1]])
        assert_array_equal(grid.cell_centers, [[2.5, 2.0], [3.5, 2.0]])

        assert_array_equal(grid.cell_types, [CellType.QUAD.value, CellType.QUAD.value])

    def test_unstructured(self):
        grid = UnstructuredGrid(
            points=[
                [0.0, 0.0],
                [0.0, 2.0],
                [2.0, 2.0],
                [2.0, 0.0],
                [2.0, 0.0],
                [2.0, 2.0],
                [4.0, 2.0],
                [4.0, 0.0],
            ],
            cells=[[0, 1, 2, 3], [4, 5, 6, 7]],
            cell_types=[CellType.QUAD.value, CellType.QUAD.value],
        )

        self.assertEqual(grid.dim, 2)
        self.assertEqual(grid.point_count, 8)
        self.assertEqual(grid.cell_count, 2)
        self.assertEqual(grid.data_shape, (2,))
        self.assertEqual(grid.data_size, 2)

        assert_array_equal(grid.cell_types, [3, 3])
        assert_array_equal(grid.cell_centers, [[1.0, 1.0], [3.0, 1.0]])
        assert_array_equal(grid.cell_node_counts, [4, 4])
        assert_array_equal(grid.data_points, [[1.0, 1.0], [3.0, 1.0]])
