import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from finam import CellType, EsriGrid, NoGrid, UniformGrid, UnstructuredGrid
from finam.data.grid_tools import (
    check_axes_monotonicity,
    check_axes_uniformity,
    flatten_cells,
    gen_axes,
    gen_cells,
    gen_node_centers,
    gen_points,
    order_map,
    point_order,
)


class TestGridTools(unittest.TestCase):
    def test_point_order(self):
        self.assertEqual(point_order(order="C", axes_reversed=False), "C")
        self.assertEqual(point_order(order="C", axes_reversed=True), "F")
        self.assertEqual(point_order(order="F", axes_reversed=False), "F")
        self.assertEqual(point_order(order="F", axes_reversed=True), "C")

    def test_order_map(self):
        assert_array_equal(order_map((2, 3), of="C", to="C"), [0, 1, 2, 3, 4, 5])
        assert_array_equal(order_map((2, 3), of="F", to="F"), [0, 1, 2, 3, 4, 5])
        assert_array_equal(order_map((2, 3), of="F", to="C"), [0, 2, 4, 1, 3, 5])
        assert_array_equal(order_map((2, 3), of="C", to="F"), [0, 3, 1, 4, 2, 5])

    def test_gen_node_centers(self):
        uniform = UniformGrid((2, 3), (2.0, 2.0, 2.0), (1.0, 1.0, 1.0))
        assert_allclose(gen_node_centers(uniform), [[2.0, 2.0], [2.0, 4.0]])

        unstruct = UnstructuredGrid(
            points=[[0.0, 0.0], [0.0, 3.0], [3.0, 0.0]],
            cells=[0, 1, 2],
            cell_types=[CellType.TRI.value],
        )
        assert_allclose(gen_node_centers(unstruct), [[1.0, 1.0]])

        unstruct = UnstructuredGrid(
            points=[[0.0, 0.0], [0.0, 2.0], [2.0, 2.0], [2.0, 0.0]],
            cells=[0, 1, 2, 3],
            cell_types=[CellType.QUAD.value],
        )
        assert_allclose(gen_node_centers(unstruct), [[1.0, 1.0]])

    def test_gen_axes(self):
        axes = gen_axes((3, 4), (2.0, 3.0), (1.0, 1.0))
        assert_allclose(axes[0], [1.0, 3.0, 5.0])
        assert_allclose(axes[1], [1.0, 4.0, 7.0, 10.0])

        axes = gen_axes((3, 4), (2.0, 3.0), (1.0, 1.0), (False, False))
        assert_allclose(axes[0], [5.0, 3.0, 1.0])
        assert_allclose(axes[1], [10.0, 7.0, 4.0, 1.0])

    def test_gen_points(self):
        axes = gen_axes((3, 4), (2.0, 3.0), (1.0, 1.0))
        points = gen_points(axes)
        assert_allclose(
            points[:6],
            [[1.0, 1.0], [3.0, 1.0], [5.0, 1.0], [1.0, 4.0], [3.0, 4.0], [5.0, 4.0]],
        )

        axes = gen_axes((3, 4), (2.0, 3.0), (1.0, 1.0))
        points = gen_points(axes, order="C")
        assert_allclose(
            points[:6],
            [[1.0, 1.0], [1.0, 4.0], [1.0, 7.0], [1.0, 10.0], [3.0, 1.0], [3.0, 4.0]],
        )

        axes = gen_axes((3, 4), (2.0, 3.0), (1.0, 1.0), (False, False))
        points = gen_points(axes, order="C", axes_increase=(False, False))
        assert_allclose(
            points[:6],
            [[1.0, 1.0], [1.0, 4.0], [1.0, 7.0], [1.0, 10.0], [3.0, 1.0], [3.0, 4.0]],
        )

    def test_gen_cells(self):
        assert_array_equal(gen_cells((), order="F"), [[0]])
        assert_array_equal(gen_cells((1,), order="F"), [[0]])
        assert_array_equal(gen_cells((2,), order="F"), [[0, 1]])

        assert_array_equal(gen_cells((2, 2, 2), order="F"), [[2, 3, 1, 0, 6, 7, 5, 4]])

        # 0---1---2
        # |   |   |
        # 3-->4-->5
        assert_array_equal(gen_cells((3, 2), order="F"), [[3, 4, 1, 0], [4, 5, 2, 1]])
        # 0---1
        # |   |
        # 2-->3
        # |   |
        # 4-->5
        assert_array_equal(gen_cells((2, 3), order="F"), [[2, 3, 1, 0], [4, 5, 3, 2]])
        # 0---2---4
        # |   |   |
        # 1-->3-->5
        assert_array_equal(gen_cells((3, 2), order="C"), [[1, 3, 2, 0], [3, 5, 4, 2]])
        # 0---3
        # |   |
        # 1-->4
        # |   |
        # 2-->5
        assert_array_equal(gen_cells((2, 3), order="C"), [[1, 4, 3, 0], [2, 5, 4, 1]])

    def test_check_axes_monotonicity(self):
        axes = [np.asarray([0, 1, 2]), np.asarray([0, 1, 2, 3])]
        assert_array_equal(check_axes_monotonicity(axes), [True, True])
        assert_array_equal(axes[0], [0, 1, 2])
        assert_array_equal(axes[1], [0, 1, 2, 3])

        axes = [np.asarray([2, 1, 0]), np.asarray([0, 1, 2, 3])]
        assert_array_equal(check_axes_monotonicity(axes), [False, True])
        assert_array_equal(axes[0], [0, 1, 2])
        assert_array_equal(axes[1], [0, 1, 2, 3])

        axes = [np.asarray([0, 1, 2]), np.asarray([3, 2, 1, 0])]
        assert_array_equal(check_axes_monotonicity(axes), [True, False])
        assert_array_equal(axes[0], [0, 1, 2])
        assert_array_equal(axes[1], [0, 1, 2, 3])

        axes = [np.asarray([2, 1, 0]), np.asarray([3, 2, 1, 0])]
        assert_array_equal(check_axes_monotonicity(axes), [False, False])
        assert_array_equal(axes[0], [0, 1, 2])
        assert_array_equal(axes[1], [0, 1, 2, 3])

        axes = [np.asarray([2, 0, 1]), np.asarray([0, 1, 2, 3])]
        with self.assertRaises(ValueError):
            check_axes_monotonicity(axes)

        axes = [np.asarray([0, 1, 2]), np.asarray([0, 2, 1, 3])]
        with self.assertRaises(ValueError):
            check_axes_monotonicity(axes)

    def test_errors(self):
        # wrong len(axes_increase)
        with self.assertRaises(ValueError):
            UniformGrid((4, 2), axes_increase=[False])
        # wrong mesh_type
        with self.assertRaises(ValueError):
            grid = UniformGrid((2, 2))
            grid.export_vtk("test", mesh_type="wrong")
        # wrong mesh_type
        with self.assertRaises(ValueError):
            grid = UniformGrid((2, 2), data_location=None)
            grid.data_points

    def test_flatten_cells(self):
        assert_array_equal(flatten_cells(np.asarray([0, 1, 2, 3])), [0, 1, 2, 3])
        assert_array_equal(
            flatten_cells(np.asarray([[0, 1, 2, 3], [4, 5, 6, 7]])),
            [0, 1, 2, 3, 4, 5, 6, 7],
        )

    def test_axes_uniformity(self):
        assert_array_equal(
            check_axes_uniformity([np.asarray([0, 1, 2, 3]), np.asarray([0, 2, 3])]),
            [1, float("nan")],
        )

    def test_compatibility(self):
        grid1 = EsriGrid(nrows=2, ncols=3)
        grid2 = UniformGrid((4, 3))
        data1 = np.arange(6).reshape((2, 3))

        self.assertTrue(grid1.compatible_with(grid2))

        trans = grid1.get_transform_to(grid2)
        trans2 = grid2.get_transform_to(grid1)
        self.assertIsNotNone(trans)
        data2 = trans(data1)
        data3 = trans2(data2)
        assert_array_equal(data1.shape, data2.T.shape)
        assert_array_equal(data1[0], data2.T[1])
        assert_array_equal(data1[1], data2.T[0])
        assert_array_equal(data1, data3)

        grid1 = EsriGrid(nrows=2, ncols=3, cellsize=2.0)
        self.assertFalse(grid1.compatible_with(grid2))

        grid1 = EsriGrid(nrows=3, ncols=3)
        self.assertFalse(grid1.compatible_with(grid2))

        grid1 = EsriGrid(nrows=2, ncols=3)
        # layer height info results in 3D grid
        grid2 = UniformGrid((4, 3, 1))
        self.assertFalse(grid1.compatible_with(grid2))
