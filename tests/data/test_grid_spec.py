import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from finam import (
    CellType,
    EsriGrid,
    Location,
    RectilinearGrid,
    UniformGrid,
    UnstructuredGrid,
    UnstructuredPoints,
)

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


class TestGridSpec(unittest.TestCase):
    def test_uniform(self):
        grid = UniformGrid((3, 2), spacing=(1.0, 2.0), origin=(2.0, 1.0))

        self.assertEqual(grid.name, "UniformGrid")
        self.assertEqual(grid.dim, 2)
        self.assertEqual(grid.dims, (3, 2))
        self.assertEqual(grid.point_count, 6)
        self.assertEqual(grid.cell_count, 2)
        self.assertEqual(grid.data_shape, (2, 1))
        self.assertEqual(grid.axes_names, ["x", "y"])

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

        assert_array_equal(grid.cell_types, [CellType.QUAD, CellType.QUAD])

        with self.assertRaises(ValueError):
            UniformGrid((3, 2), spacing=(1.0,))

        with self.assertRaises(ValueError):
            UniformGrid((3, 2), origin=(0.0,))

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "test"
            grid.export_vtk(
                path=path, data={"data": np.zeros(grid.data_shape)}, mesh_type="uniform"
            )
            grid.export_vtk(
                path=path,
                data={"data": np.zeros(grid.data_shape)},
                mesh_type="structured",
            )
            grid.export_vtk(
                path=path,
                data={"data": np.zeros(grid.data_shape)},
                mesh_type="unstructured",
            )

        grid = UniformGrid(
            (3, 2), spacing=(1.0, 2.0), origin=(2.0, 1.0), data_location="POINTS"
        )

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "test"
            grid.export_vtk(
                path=path, data={"data": np.zeros(grid.data_shape)}, mesh_type="uniform"
            )
            grid.export_vtk(
                path=path,
                data={"data": np.zeros(grid.data_shape)},
                mesh_type="structured",
            )
            grid.export_vtk(
                path=path,
                data={"data": np.zeros(grid.data_shape)},
                mesh_type="unstructured",
            )

    def test_rectilinear(self):
        grid = RectilinearGrid([np.asarray([2.0, 3.0, 4.0]), np.asarray([1.0, 3.0])])

        self.assertEqual(grid.name, "RectilinearGrid")
        self.assertIsNone(grid.crs)
        self.assertEqual(grid.dim, 2)
        self.assertEqual(grid.dims, (3, 2))
        self.assertEqual(grid.point_count, 6)
        self.assertEqual(grid.cell_count, 2)
        self.assertEqual(grid.data_shape, (2, 1))
        self.assertEqual(grid.axes_names, ["x", "y"])

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

        assert_array_equal(grid.cell_types, [CellType.QUAD, CellType.QUAD])

        with self.assertRaises(ValueError):
            RectilinearGrid(
                [np.asarray([2.0, 3.0]), np.asarray([1.0, 3.0])], axes_names=["X"]
            )

        with self.assertRaises(ValueError):
            RectilinearGrid(
                [np.asarray([2.0, 3.0]), np.asarray([1.0, 3.0])],
                axes_attributes=[{1: 1}],
            )

        grid = RectilinearGrid([np.asarray([1.0]), np.asarray([2.0, 1.0])])
        assert_array_equal(grid.axes_increase, [True, False])

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
            cell_types=[CellType.QUAD, CellType.QUAD],
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

        with self.assertRaises(ValueError):
            UnstructuredGrid(
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
                cell_types=[CellType.QUAD, CellType.QUAD],
                axes_names=["to_few"],
            )

        with self.assertRaises(ValueError):
            UnstructuredPoints(points=[[0.0, 0.0]], axes_attributes=[{"too": "short"}])

        self.assertEqual(grid.name, "UnstructuredGrid")
        self.assertEqual(grid2.name, "UnstructuredPoints")
        self.assertIsNone(grid.crs)
        self.assertEqual(grid.dim, 2)
        self.assertEqual(grid.order, "C")
        self.assertEqual(grid.mesh_dim, 2)
        self.assertEqual(grid.point_count, 8)
        self.assertEqual(grid.cell_count, 2)
        self.assertEqual(grid.data_shape, (2,))
        self.assertEqual(grid.data_size, 2)
        self.assertEqual(grid.axes_names, ["x", "y"])

        assert_array_equal(grid.cell_types, [3, 3])
        assert_allclose(grid.cell_centers, [[1.0, 1.0], [3.0, 1.0]])
        assert_array_equal(grid.cell_node_counts, [4, 4])
        assert_allclose(grid.data_points, [[1.0, 1.0], [3.0, 1.0]])

        assert_allclose(grid.points, grid2.points)
        assert_allclose(grid.points, grid2.cell_centers)
        self.assertEqual(grid2.dim, 2)
        self.assertEqual(grid2.mesh_dim, 0)
        assert_allclose(grid2.cell_node_counts, 1)

        with self.assertRaises(ValueError):
            grid2.data_location = Location.CELLS

    def test_esri(self):
        header = {
            "ncols": 520,
            "nrows": 600,
            "xllcenter": 4375050.0,
            "yllcenter": 2700050.0,
            "cellsize": 100.0,
        }
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.txt"
            write_asc(path, header)
            grid = EsriGrid.from_file(path)
        self.assertEqual(grid.name, "EsriGrid")
        self.assertAlmostEqual(grid.ncols, header["ncols"])
        self.assertAlmostEqual(grid.nrows, header["nrows"])
        self.assertAlmostEqual(grid.cellsize, header["cellsize"])
        self.assertAlmostEqual(grid.xllcorner, 4375000)
        self.assertAlmostEqual(grid.yllcorner, 2700000)

        # casting
        grid2 = grid.to_uniform()
        grid3 = grid.to_rectilinear()
        grid4 = grid2.to_rectilinear()
        self.assertTrue(grid == grid2)
        self.assertTrue(grid == grid3)
        self.assertTrue(grid == grid4)
        self.assertTrue(grid2 == grid3)
        self.assertTrue(grid2 == grid4)
        self.assertTrue(grid3 == grid4)

        with self.assertRaises(ValueError):
            grid.data_location = Location.POINTS

    def test_data_location(self):
        grid1 = UniformGrid((1,), data_location=0)
        grid2 = UniformGrid((2, 2), data_location="CELLS")
        grid3 = UniformGrid((2, 2), data_location=Location.CELLS)
        grid4 = UniformGrid((2, 2), data_location=1)
        grid5 = UniformGrid((2, 2), data_location="POINTS")
        grid6 = UniformGrid((2, 2), data_location=Location.POINTS)
        self.assertEqual(grid1.data_location, Location.CELLS)
        self.assertEqual(grid2.data_location, Location.CELLS)
        self.assertEqual(grid3.data_location, Location.CELLS)
        self.assertEqual(grid4.data_location, Location.POINTS)
        self.assertEqual(grid5.data_location, Location.POINTS)
        self.assertEqual(grid6.data_location, Location.POINTS)

    def test_cast(self):
        grid = EsriGrid(3, 2)
        us_grid = grid.to_unstructured()
        assert_allclose(grid.data_points, us_grid.data_points)
        self.assertIsInstance(us_grid, UnstructuredGrid)

    def test_copy(self):
        grid = EsriGrid(3, 2)
        us_grid = grid.to_unstructured()
        cp_grid1 = us_grid.copy()
        cp_grid2 = us_grid.copy(deep=True)

        self.assertTrue(us_grid == cp_grid1)
        self.assertTrue(us_grid == cp_grid2)

        # shallow copy shares info
        cp_grid1.points[0, 0] = 0.1
        self.assertTrue(us_grid == cp_grid1)
        self.assertFalse(us_grid == cp_grid2)

    def test_location_check(self):
        grid_s1 = UniformGrid((2, 2), data_location="CELLS")
        grid_s2 = UniformGrid((2, 2), data_location="POINTS")
        grid_u1 = grid_s1.to_unstructured()
        grid_u2 = grid_s2.to_unstructured()
        self.assertTrue(grid_s1.compatible_with(grid_s2, check_location=False))
        self.assertFalse(grid_s1.compatible_with(grid_s2, check_location=True))
        self.assertTrue(grid_u1.compatible_with(grid_u2, check_location=False))
        self.assertFalse(grid_u1.compatible_with(grid_u2, check_location=True))

    def test_equality(self):
        grid1 = UniformGrid((2, 2), data_location=0)
        grid2 = UnstructuredGrid(
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
            cell_types=[CellType.QUAD, CellType.QUAD],
            axes_names=["x", "y"],
        )

        self.assertNotEqual(grid1, 0)
        self.assertNotEqual(grid1, grid2)

    def test_cell_types(self):
        grid = UniformGrid((0,))
        self.assertEqual(grid.cell_types, [CellType.VERTEX])

        grid = UniformGrid((1,))
        assert_array_equal(grid.cell_types, [CellType.VERTEX])

        grid = UniformGrid((2,))
        assert_array_equal(grid.cell_types, [CellType.LINE])

        grid = UniformGrid((3,))
        assert_array_equal(grid.cell_types, [CellType.LINE, CellType.LINE])

        grid = UniformGrid((2, 2))
        assert_array_equal(grid.cell_types, [CellType.QUAD])
        grid = UniformGrid((2, 3))
        assert_array_equal(grid.cell_types, [CellType.QUAD, CellType.QUAD])

        grid = UniformGrid((2, 2, 2))
        assert_array_equal(grid.cell_types, [CellType.HEX])
        grid = UniformGrid((2, 2, 3))
        assert_array_equal(grid.cell_types, [CellType.HEX, CellType.HEX])


if __name__ == "__main__":
    unittest.main()
