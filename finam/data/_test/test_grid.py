import unittest

from ..grid import Grid, GridSpec


class TestGrid(unittest.TestCase):
    def test_subclassing(self):
        grid = Grid(GridSpec(10, 5))
        grid_1 = grid + 1
        self.assertEqual(grid_1.__class__, Grid)
        self.assertEqual(grid_1[0], 1)

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

        self.assertEqual(grid.to_cell(10500, 5500), (0, 0))
        self.assertEqual(grid.to_xy(0, 0), (10500, 5500))

        self.assertEqual(grid.to_cell(12500, 6500), (2, 1))
        self.assertEqual(grid.to_xy(2, 1), (12500, 6500))

    def test_set_get(self):
        spec = GridSpec(10, 5)
        grid = Grid(spec)

        grid.set(1, 2, 1.0)

        self.assertEqual(grid.get(0, 0), 0.0)
        self.assertEqual(grid.get(1, 2), 1.0)


if __name__ == "__main__":
    unittest.main()
