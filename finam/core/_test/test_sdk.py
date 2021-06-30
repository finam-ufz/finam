"""
Unit tests for the sdk implementations.
"""

import unittest

from ..interfaces import ComponentStatus
from ..sdk import AAdapter, CallbackInput, ATimeComponent, Output


class MockupAdapter(AAdapter):
    def __init__(self):
        super().__init__()

    def get_data(self, time):
        return time


class MockupComponent(ATimeComponent):
    pass


class TestComponent(unittest.TestCase):
    def test_component_status(self):
        component = MockupComponent()

        self.assertEqual(component.time(), 0)

        component._status = ComponentStatus.CREATED
        component.initialize()

        component._status = ComponentStatus.FINALIZED
        with self.assertRaises(AssertionError):
            component.initialize()

        component._status = ComponentStatus.INITIALIZED
        component.connect()

        component._status = ComponentStatus.FINALIZED
        with self.assertRaises(AssertionError):
            component.connect()

        component._status = ComponentStatus.CONNECTED
        component.validate()

        component._status = ComponentStatus.FINALIZED
        with self.assertRaises(AssertionError):
            component.validate()

        component._status = ComponentStatus.VALIDATED
        component.update()

        component._status = ComponentStatus.UPDATED
        component.update()

        component._status = ComponentStatus.FINALIZED
        with self.assertRaises(AssertionError):
            component.update()

        component._status = ComponentStatus.UPDATED
        component.finalize()

        component._status = ComponentStatus.FINALIZED
        with self.assertRaises(AssertionError):
            component.update()


class TestChaining(unittest.TestCase):
    def test_chaining(self):
        adapter1 = MockupAdapter()
        adapter2 = MockupAdapter()
        adapter3 = MockupAdapter()

        adapter1 >> adapter2 >> adapter3

        self.assertEqual(adapter1.targets, [adapter2])
        self.assertEqual(adapter2.targets, [adapter3])

        self.assertEqual(adapter2.source, adapter1)
        self.assertEqual(adapter3.source, adapter2)

    def test_multiple_sources(self):
        adapter1 = MockupAdapter()
        adapter2 = MockupAdapter()
        adapter3 = MockupAdapter()

        adapter1 >> adapter3

        with self.assertRaises(AssertionError) as context:
            adapter2 >> adapter3

        self.assertTrue("Source of input is already set!" in str(context.exception))


class TestOutput(unittest.TestCase):
    def test_push_notify(self):
        counter = 0

        def callback(clr, time):
            nonlocal counter
            counter += 1

        out = Output()
        inp = CallbackInput(callback=callback)

        out >> inp

        out.push_data(100, 0)

        self.assertEqual(out.get_data(0), 100)
        self.assertEqual(inp.pull_data(0), 100)
        self.assertEqual(counter, 1)


class TestCallbackInput(unittest.TestCase):
    def test_callback_input(self):
        caller = None
        counter = 0

        def callback(clr, time):
            nonlocal caller
            nonlocal counter
            caller = clr
            counter += 1

        inp = CallbackInput(callback=callback)

        inp.source_changed(0.0)

        self.assertEqual(caller, inp)
        self.assertEqual(counter, 1)


if __name__ == "__main__":
    unittest.main()
