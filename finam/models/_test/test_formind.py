import unittest

from ..formind_mpi import SoilWaterAdapter
from data.grid import Grid, GridSpec
from modules.generators import CallbackGenerator


def create_grid(value):
    grid = Grid(GridSpec(1, 1))
    grid.fill(value)
    return grid


class TestAdapter(unittest.TestCase):
    def test_reduction_factor(self):
        values = ([20] * 10) + ([22] * 10) + ([24] * 10) + ([20] * 5) + ([24] * 5)

        self.source = CallbackGenerator(
            callbacks={"SW": lambda t: create_grid(values[t])}, step=1
        )
        self.adapter = SoilWaterAdapter(20.0, 30.0)

        self.source.initialize()

        self.source.outputs()["SW"] >> self.adapter

        self.source.connect()
        self.source.validate()

        self.assertEqual(self.adapter.get_data(0)[0], 0.0)

        # 10x low soil water (actually, 9x)
        for i in range(1, 10):
            self.source.update()

        self.assertEqual(self.adapter.get_data(0)[0], 0.0)

        # 10x medium soil water
        for i in range(10):
            self.source.update()

        self.assertEqual(self.adapter.get_data(0)[0], 0.5)

        # 10x high soil water
        for i in range(10):
            self.source.update()

        self.assertEqual(self.adapter.get_data(0)[0], 1.0)

        # 5x high, 5x low soil water
        for i in range(10):
            self.source.update()

        self.assertEqual(self.adapter.get_data(0)[0], 0.5)


if __name__ == "__main__":
    unittest.main()
