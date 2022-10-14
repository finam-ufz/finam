"""
Unit tests for the sdk implementations.
"""

import unittest
from datetime import datetime

from finam.core.interfaces import ComponentStatus, FinamLogError, FinamStatusError
from finam.core.schedule import Composition
from finam.core.sdk import (
    AAdapter,
    ATimeComponent,
    CallbackInput,
    Input,
    IOList,
    Output,
)
from finam.data import Info, NoGrid


class MockupAdapter(AAdapter):
    def __init__(self):
        super().__init__()

    def get_data(self, time):
        return time


class MockupComponent(ATimeComponent):
    def __init__(self):
        super().__init__()
        self._time = datetime(2000, 1, 1)
        self.status = ComponentStatus.CREATED


class TestComponent(unittest.TestCase):
    def test_component_status(self):
        component = MockupComponent()

        self.assertEqual(component.time, datetime(2000, 1, 1))
        self.assertEqual(component.status, ComponentStatus.CREATED)

        composition = Composition([component])

        with self.assertRaises(FinamStatusError):
            composition.initialize()


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

        with self.assertRaises(ValueError) as context:
            adapter2 >> adapter3

        self.assertTrue("Source of input is already set!" in str(context.exception))


class TestOutput(unittest.TestCase):
    def test_push_notify(self):
        counter = 0
        t = datetime(2000, 1, 1)
        info = Info(grid=NoGrid(), meta={"test": 0})

        def callback(clr, time):
            nonlocal counter
            counter += 1

        out = Output(name="Output")
        inp = CallbackInput(callback=callback, name="Callback")

        out >> inp

        out.push_info(info)
        out.push_data(100, t)

        self.assertTrue(inp.has_source)
        self.assertTrue(out.has_targets)
        self.assertEqual(out.get_info(info), info)
        self.assertEqual(out.get_data(t), 100)
        self.assertEqual(inp.exchange_info(info), info)
        self.assertEqual(inp.pull_data(t), 100)
        self.assertEqual(counter, 1)


class TestCallbackInput(unittest.TestCase):
    def test_callback_input(self):
        caller = None
        counter = 0
        t = datetime(2000, 1, 1)

        def callback(clr, time):
            nonlocal caller
            nonlocal counter
            caller = clr
            counter += 1

        inp = CallbackInput(callback=callback, name="callback")

        inp.source_changed(t)

        self.assertEqual(caller, inp)
        self.assertEqual(counter, 1)


class TestIOList(unittest.TestCase):
    def test_io_list(self):
        inp = Input("test1")
        out = Output("test2")
        inp_list = IOList("INPUT")
        out_list = IOList("OUTPUT")

        # io setting
        inp_list.add(inp)
        out_list["test2"] = out
        inp_list.add(name="test0")

        # wrong type
        with self.assertRaises(ValueError):
            inp_list.add(out)
        with self.assertRaises(ValueError):
            out_list["test1"] = inp

        # no logger
        with self.assertRaises(FinamLogError):
            inp_list.set_logger(None)

        # already present
        with self.assertRaises(ValueError):
            inp_list["test1"] = inp
        with self.assertRaises(ValueError):
            out_list.add(out)

        # wrong name
        with self.assertRaises(ValueError):
            inp_list["test2"] = inp

        # make frozen
        inp_list.frozen = True
        out_list.frozen = True
        with self.assertRaises(ValueError):
            inp_list["test1"] = inp
        with self.assertRaises(ValueError):
            out_list.add(name="test3")


if __name__ == "__main__":
    unittest.main()
