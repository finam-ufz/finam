import unittest

import numpy as np
import numpy.ma as ma

from finam.data.grid import Grid, GridArray, GridSpec


class TestGridSpec(unittest.TestCase):
    def test_grid_spec(self):
        s1 = GridSpec(10, 5, dtype=float)
        s2 = GridSpec(10, 5, dtype=int)
        s3 = GridSpec(10, 6)

        self.assertEqual(s1, s2)
        self.assertNotEqual(s1, s3)

        s1.xll = 1.0
        self.assertNotEqual(s1, s2)

        s1.xll = 0.0
        s1.cell_size = 10.0
        self.assertNotEqual(s1, s2)


class TestGridArray(unittest.TestCase):
    def test_wrong_data(self):
        spec = GridSpec(3, 2)
        _grid = GridArray(spec, data=np.zeros(2 * 3))

        with self.assertRaises(ValueError):
            _grid = GridArray(spec, data=np.zeros(2 * 3 + 1))


class TestGrid(unittest.TestCase):
    def test_subclassing(self):
        grid = Grid(GridSpec(10, 5))
        grid_1 = grid + 1
        self.assertEqual(grid_1.__class__, Grid)
        self.assertEqual(grid_1[0], 1)

    def test_wrong_data(self):
        spec = GridSpec(3, 2)
        _grid = Grid(spec, data=np.zeros(2 * 3))

        with self.assertRaises(ValueError):
            _grid = Grid(spec, data=np.zeros(2 * 3 + 1))

    def test_create_like(self):
        spec = GridSpec(20, 10)
        grid1 = Grid(spec)
        grid2 = Grid.create_like(grid1)

        self.assertEqual(grid2.__class__, Grid)
        self.assertEqual(grid1.spec, grid2.spec)
        self.assertEqual(grid1.no_data, grid2.no_data)

    def test_contains(self):
        spec = GridSpec(20, 10)
        grid = Grid(spec)

        self.assertTrue(grid.contains(0, 0))
        self.assertTrue(grid.contains(19, 9))

        self.assertFalse(grid.contains(-1, 0))
        self.assertFalse(grid.contains(20, 0))
        self.assertFalse(grid.contains(0, -1))
        self.assertFalse(grid.contains(0, 10))

    def test_coordinate_conversion(self):
        spec = GridSpec(20, 10, cell_size=1000, xll=10000, yll=5000)
        grid = Grid(spec)

        self.assertEqual(grid.to_cell(10500, 5500), (0, 9))
        self.assertEqual(grid.to_xy(0, 9), (10500, 5500))

        self.assertEqual(grid.to_cell(12500, 6500), (2, 8))
        self.assertEqual(grid.to_xy(2, 8), (12500, 6500))

    def test_set_get(self):
        spec = GridSpec(10, 5)
        grid = Grid(spec)

        grid.set(1, 2, 1.0)

        self.assertEqual(grid.get(0, 0), 0.0)
        self.assertEqual(grid.get(1, 2), 1.0)

    def test_with_data(self):
        spec = GridSpec(10, 5)
        grid = Grid(spec, data=np.zeros(10 * 5))

        grid.set(1, 2, 1.0)

        self.assertEqual(grid.get(0, 0), 0.0)
        self.assertEqual(grid.get(1, 2), 1.0)

    def test_mask(self):
        spec = GridSpec(10, 5)
        data = np.zeros(10 * 5)
        data[1] = -9999
        grid = Grid(spec, data=data)

        self.assertEqual(grid.get(0, 0), 0.0)
        self.assertIs(grid.get(1, 0), ma.masked)

        self.assertEqual(grid.is_masked(0, 0), False)
        self.assertEqual(grid.is_masked(1, 0), True)

        grid.set_masked(2, 3)
        self.assertEqual(grid.is_masked(2, 3), True)

    def test_mask_calc(self):
        spec = GridSpec(3, 2)

        data1 = [
            1,
            1,
            1,
            1,
            -9999,
            1,
        ]
        grid1 = Grid(spec, data=data1)

        data2 = [
            2,
            2,
            2,
            2,
            2,
            -9999,
        ]
        grid2 = Grid(spec, data=data2)

        np.testing.assert_almost_equal(
            grid1.mask, [False, False, False, False, True, False]
        )
        np.testing.assert_almost_equal(grid1.data, data1)

        np.testing.assert_almost_equal(
            grid2.mask, [False, False, False, False, False, True]
        )
        np.testing.assert_almost_equal(grid2.data, data2)

        grid3 = grid1 + grid2
        filled = grid3.filled()
        self.assertEqual(grid3.__class__, Grid)
        self.assertEqual(filled.__class__, GridArray)
        np.testing.assert_almost_equal(
            grid3.mask, [False, False, False, False, True, True]
        )
        np.testing.assert_almost_equal(filled, [3, 3, 3, 3, -9999, -9999])


if __name__ == "__main__":
    unittest.main()
