"""
Unit tests for the driver/scheduler.
"""

import unittest

from ..interfaces import ComponentStatus
from ..schedule import Composition
from modules.generators import CallbackGenerator
from modules.writers import CsvWriter
from adapters.base import Callback
from adapters.time import LinearIntegration


class TestComposition(unittest.TestCase):
    def test_init_run(self):
        module = CallbackGenerator(callbacks={"Output": lambda t: t}, step=1)
        composition = Composition([module])
        composition.initialize()

        self.assertEqual(module.status(), ComponentStatus.INITIALIZED)
        self.assertEqual(len(module.outputs()), 1)

        composition.run(t_max=2.0)

        self.assertEqual(module.status(), ComponentStatus.FINALIZED)
        self.assertEqual(module.time(), 2)

    def test_validate_branching(self):
        module = CallbackGenerator(callbacks={"Output": lambda t: t}, step=1)
        composition = Composition([module])
        composition.initialize()

        non_branching_adapter = (
            module.outputs()["Output"]
            >> LinearIntegration.mean()
            >> Callback(callback=lambda data, time: data)
        )

        non_branching_adapter >> Callback(callback=lambda data, time: data)
        non_branching_adapter >> Callback(callback=lambda data, time: data)

        with self.assertRaises(AssertionError) as context:
            composition.validate()

        self.assertTrue("Disallowed branching" in str(context.exception))

    def test_validate_inputs(self):
        module = CsvWriter(path="test.csv", step=1, inputs=["Input"])
        composition = Composition([module])
        composition.initialize()

        with self.assertRaises(AssertionError) as context:
            composition.validate()

        self.assertTrue("Unconnected input" in str(context.exception))


if __name__ == "__main__":
    unittest.main()
