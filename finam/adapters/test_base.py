import unittest

from modules.generators import CallbackGenerator
from .base import Callback


class TestCallback(unittest.TestCase):
    def setUp(self):
        self.source = CallbackGenerator(callbacks={"Step": lambda t: t}, step=1)
        self.adapter = Callback(callback=lambda v, t: v * 2)

        self.source.initialize()

        self.source.outputs()["Step"] >> self.adapter

        self.source.validate()

    def test_callback_adapter(self):
        self.assertEqual(self.adapter.get_data(0), 0)
        self.source.update()
        self.assertEqual(self.adapter.get_data(0), 2)
        self.source.update()
        self.assertEqual(self.adapter.get_data(0), 4)


if __name__ == "__main__":
    unittest.main()
