import unittest

from modules.generators import CallbackGenerator
from data.grid import Grid, GridSpec
from .time import LinearInterpolation, LinearIntegration, NextValue, PreviousValue


class TestNextValue(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(callbacks={"Step": lambda t: t}, step=1)
        self.adapter = NextValue()

        self.source.initialize()

        self.source.outputs()["Step"] >> self.adapter

        self.source.validate()

    def test_next_value(self):
        self.assertEqual(self.adapter.get_data(0.0), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(0.5), 1.0)
        self.assertEqual(self.adapter.get_data(1.0), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(1.5), 2.0)
        self.assertEqual(self.adapter.get_data(2.0), 2.0)


class TestPreviousValue(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(callbacks={"Step": lambda t: t}, step=1)
        self.adapter = PreviousValue()

        self.source.initialize()

        self.source.outputs()["Step"] >> self.adapter

        self.source.validate()

    def test_previous_value(self):
        self.assertEqual(self.adapter.get_data(0.0), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(0.5), 0.0)
        self.assertEqual(self.adapter.get_data(1.0), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(1.5), 1.0)
        self.assertEqual(self.adapter.get_data(2.0), 2.0)


class TestLinearInterpolation(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(callbacks={"Step": lambda t: t}, step=1)
        self.adapter = LinearInterpolation()

        self.source.initialize()
        self.source.outputs()["Step"] >> self.adapter
        self.source.validate()

    def test_linear_interpolation(self):
        self.assertEqual(self.adapter.get_data(0.0), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(0.5), 0.5)
        self.assertEqual(self.adapter.get_data(1.0), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(1.5), 1.5)
        self.assertEqual(self.adapter.get_data(2.0), 2.0)


def create_grid(t):
    grid = Grid(GridSpec(10, 5))
    grid.fill(t)
    return grid


class TestLinearGridInterpolation(unittest.TestCase):

    def setUp(self):
        self.source = CallbackGenerator(callbacks={"Grid": lambda t: create_grid(t)}, step=1)
        self.adapter = LinearInterpolation()

        self.source.initialize()
        self.source.outputs()["Grid"] >> self.adapter
        self.source.validate()

    def test_linear_grid_interpolation(self):
        self.assertEqual(self.adapter.get_data(0.0).get(2, 3), 0.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(0.5).get(2, 3), 0.5)
        self.assertEqual(self.adapter.get_data(1.0).get(2, 3), 1.0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(1.5).get(2, 3), 1.5)
        self.assertEqual(self.adapter.get_data(2.0).get(2, 3), 2.0)


class TestLinearIntegration(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(callbacks={"Step": lambda t: t}, step=1)
        self.adapter = LinearIntegration.sum()

        self.source.initialize()

        self.source.outputs()["Step"] >> self.adapter

        self.source.validate()

    def test_linear_integration_adapter(self):
        self.source.update()
        self.assertEqual(self.adapter.get_data(0.5), 0.125)
        self.assertEqual(self.adapter.get_data(1.0), 0.375)
        self.source.update()
        self.source.update()
        self.assertEqual(self.adapter.get_data(3.0), 4.0)


if __name__ == "__main__":
    unittest.main()
