import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from finam.data.grid_spec import (
    EsriGrid,
    RectilinearGrid,
    UniformGrid,
    UnstructuredGrid,
    UnstructuredPoints,
)
from finam.data.grid_tools import CellType

HEADER = [
    "ncols",
    "nrows",
    "xllcorner",
    "yllcorner",
    "xllcenter",
    "yllcenter",
    "cellsize",
    "NODATA_value",
]


def write_asc(file, info):
    with open(file, "w") as f:
        for val in HEADER:
            if val not in info:
                continue
            print(f"{val:<12}", info[val], file=f)


class TestUniform(unittest.TestCase):
    def test_uniform(self):
        grid = UniformGrid((3, 2), spacing=(1.0, 2.0), origin=(2.0, 1.0))

        self.assertEqual(grid.dim, 2)
        self.assertEqual(grid.dims, (3, 2))
        self.assertEqual(grid.point_count, 6)
        self.assertEqual(grid.cell_count, 2)
        self.assertEqual(grid.data_shape, (2, 1))

        assert_allclose(grid.axes[0], [2.0, 3.0, 4.0])
        assert_allclose(grid.axes[1], [1.0, 3.0])

        assert_allclose(grid.cell_axes[0], [2.5, 3.5])
        assert_allclose(grid.cell_axes[1], [2.0])

        assert_allclose(grid.data_axes[0], [2.5, 3.5])
        assert_allclose(grid.data_axes[1], [2.0])

        assert_allclose(
            grid.points,
            [[2.0, 1.0], [3.0, 1.0], [4.0, 1.0], [2.0, 3.0], [3.0, 3.0], [4.0, 3.0]],
        )
        assert_array_equal(grid.cells, [[3, 4, 1, 0], [4, 5, 2, 1]])
        assert_allclose(grid.cell_centers, [[2.5, 2.0], [3.5, 2.0]])

        assert_array_equal(grid.cell_types, [CellType.QUAD.value, CellType.QUAD.value])

        with self.assertRaises(ValueError):
            UniformGrid((3, 2), spacing=(1.0,))

        with self.assertRaises(ValueError):
            UniformGrid((3, 2), origin=(0.0,))

        grid.export_vtk(
            path="test", data={"data": np.zeros(grid.data_shape)}, mesh_type="uniform"
        )
        grid.export_vtk(
            path="test",
            data={"data": np.zeros(grid.data_shape)},
            mesh_type="structured",
        )
        grid.export_vtk(
            path="test",
            data={"data": np.zeros(grid.data_shape)},
            mesh_type="unstructured",
        )

    def test_rectilinear(self):
        grid = RectilinearGrid([np.asarray([2.0, 3.0, 4.0]), np.asarray([1.0, 3.0])])

        self.assertIsNone(grid.crs)
        self.assertEqual(grid.dim, 2)
        self.assertEqual(grid.dims, (3, 2))
        self.assertEqual(grid.point_count, 6)
        self.assertEqual(grid.cell_count, 2)
        self.assertEqual(grid.data_shape, (2, 1))

        assert_allclose(grid.axes[0], [2.0, 3.0, 4.0])
        assert_allclose(grid.axes[1], [1.0, 3.0])

        assert_allclose(grid.cell_axes[0], [2.5, 3.5])
        assert_allclose(grid.cell_axes[1], [2.0])

        assert_allclose(grid.data_axes[0], [2.5, 3.5])
        assert_allclose(grid.data_axes[1], [2.0])

        assert_allclose(
            grid.points,
            [[2.0, 1.0], [3.0, 1.0], [4.0, 1.0], [2.0, 3.0], [3.0, 3.0], [4.0, 3.0]],
        )
        assert_array_equal(grid.cells, [[3, 4, 1, 0], [4, 5, 2, 1]])
        assert_allclose(grid.cell_centers, [[2.5, 2.0], [3.5, 2.0]])

        assert_array_equal(grid.cell_types, [CellType.QUAD.value, CellType.QUAD.value])

        with self.assertRaises(ValueError):
            RectilinearGrid(
                [np.asarray([2.0, 3.0]), np.asarray([1.0, 3.0])], axes_names=["X"]
            )

        with self.assertRaises(ValueError):
            RectilinearGrid(
                [np.asarray([2.0, 3.0]), np.asarray([1.0, 3.0])],
                axes_attributes=[{1: 1}],
            )

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
        grid2 = UnstructuredPoints(
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
        )
        self.assertIsNone(grid.crs)
        self.assertEqual(grid.dim, 2)
        self.assertEqual(grid.point_count, 8)
        self.assertEqual(grid.cell_count, 2)
        self.assertEqual(grid.data_shape, (2,))
        self.assertEqual(grid.data_size, 2)

        assert_array_equal(grid.cell_types, [3, 3])
        assert_allclose(grid.cell_centers, [[1.0, 1.0], [3.0, 1.0]])
        assert_array_equal(grid.cell_node_counts, [4, 4])
        assert_allclose(grid.data_points, [[1.0, 1.0], [3.0, 1.0]])

        assert_allclose(grid.points, grid2.points)
        assert_allclose(grid.points, grid2.cell_centers)
        self.assertEqual(grid2.dim, 2)
        self.assertEqual(grid2.mesh_dim, 0)
        assert_allclose(grid2.cell_node_counts, 1)

    def test_esri(self):
        header = {
            "ncols": 520,
            "nrows": 600,
            "xllcenter": 4375050.0,
            "yllcenter": 2700050.0,
            "cellsize": 100.0,
        }
        write_asc("test.txt", header)
        grid = EsriGrid.from_file("test.txt")
        self.assertAlmostEqual(grid.ncols, header["ncols"])
        self.assertAlmostEqual(grid.nrows, header["nrows"])
        self.assertAlmostEqual(grid.cellsize, header["cellsize"])
        self.assertAlmostEqual(grid.xllcorner, 4375000)
        self.assertAlmostEqual(grid.yllcorner, 2700000)
