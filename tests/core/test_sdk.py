"""
Unit tests for the sdk implementations.
"""

import unittest
from datetime import datetime

from finam import (
    AAdapter,
    ATimeComponent,
    CallbackInput,
    ComponentStatus,
    Composition,
    FinamLogError,
    FinamMetaDataError,
    FinamNoDataError,
    FinamStatusError,
    Info,
    Input,
    NoGrid,
)
from finam.core.sdk import IOList, Output


class MockupAdapter(AAdapter):
    def __init__(self):
        super().__init__()

    def _get_data(self, time):
        return time


class MockupComponent(ATimeComponent):
    def __init__(self):
        super().__init__()
        self._time = datetime(2000, 1, 1)
        self.status = ComponentStatus.CREATED

    def _initialize(self):
        self.status = ComponentStatus.FAILED


class MockupComponentIO(ATimeComponent):
    def __init__(self):
        super().__init__()
        self._time = datetime(2000, 1, 1)
        self.status = ComponentStatus.CREATED

    def _initialize(self):
        self.inputs.add(name="Input")
        self.outputs.add(name="Output")


class TestComponent(unittest.TestCase):
    def test_component_status(self):
        component = MockupComponent()

        self.assertEqual(component.time, datetime(2000, 1, 1))
        self.assertEqual(component.status, ComponentStatus.CREATED)

        composition = Composition([component])

        with self.assertRaises(FinamStatusError):
            composition.initialize()

    def test_connect_helper(self):
        component = MockupComponentIO()
        composition = Composition([component])
        composition.initialize()

        component.create_connector()

        self.assertTrue(component.connector is not None)
        self.assertEqual(component.connector._inputs, component.inputs)
        self.assertEqual(component.connector._outputs, component.outputs)

        component.try_connect()

        self.assertEqual(component.status, ComponentStatus.CONNECTING_IDLE)


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

        def callback(_clr, _time):
            nonlocal counter
            counter += 1

        out = Output(name="Output")
        inp = CallbackInput(callback=callback, name="Callback")

        out >> inp

        out.push_info(info)
        out.get_info(info)
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

        def callback(clr, _time):
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


class TestComponentFails(unittest.TestCase):
    def test_try_connect_fail(self):
        comp = MockupComponent()
        with self.assertRaises(FinamStatusError):
            comp.try_connect()

    def test_time_fail(self):
        comp = MockupComponent()
        comp._time = 0
        with self.assertRaises(ValueError):
            _t = comp.time

        with self.assertRaises(ValueError):
            comp.time = 0


class TestAdapter(unittest.TestCase):
    def test_adapter(self):
        adapter = MockupAdapter()
        adapter.push_data(1, datetime(2000, 1, 1))

        with self.assertRaises(ValueError):
            adapter.push_data(1, 0)

        with self.assertRaises(ValueError):
            adapter.source_changed(0)

        with self.assertRaises(FinamMetaDataError):
            adapter.exchange_info(None)

        with self.assertRaises(FinamMetaDataError):
            adapter.exchange_info(0)

        with self.assertRaises(FinamLogError):
            adapter.set_source(0)

        self.assertEqual(adapter.info, None)


class TestIOFails(unittest.TestCase):
    def test_input_output_fail(self):
        with self.assertRaises(ValueError):
            _in = Input(name=None)
        with self.assertRaises(ValueError):
            _in = Input(name="In", info=Info(grid=NoGrid()), units="m")

        with self.assertRaises(ValueError):
            _in = Output(name=None)
        with self.assertRaises(ValueError):
            _in = Output(name="In", info=Info(grid=NoGrid()), units="m")

        inp = Input(name="In", grid=NoGrid())
        out = Output(name="Out", grid=NoGrid())
        out >> inp
        with self.assertRaises(ValueError):
            inp.pull_data(0)

        inp = Input(name="In", grid=NoGrid())
        out = Output(name="Out", grid=NoGrid())
        out >> inp
        inp._in_info_exchanged = True
        with self.assertRaises(FinamMetaDataError):
            inp.exchange_info(info=Info(grid=NoGrid()))

        inp = Input(name="In")
        out = Output(name="Out", grid=NoGrid())
        out >> inp
        with self.assertRaises(FinamMetaDataError):
            inp.exchange_info(info=None)

        inp = Input(name="In", grid=NoGrid())
        out = Output(name="Out", grid=NoGrid())
        out >> inp
        with self.assertRaises(FinamMetaDataError):
            inp.exchange_info(info=Info(grid=NoGrid()))

        inp = Input(name="In")
        out = Output(name="Out", grid=NoGrid())
        out >> inp
        with self.assertRaises(FinamMetaDataError):
            inp.exchange_info(info=100)

        out = Output(name="Out", grid=NoGrid())
        with self.assertRaises(ValueError):
            out.add_target(0)

        out.push_data(0, datetime(2000, 1, 1))

        inp = Input(name="In")
        out >> inp
        with self.assertRaises(ValueError):
            out.push_data(0, 0)

        with self.assertRaises(FinamMetaDataError):
            out.push_info(0)

        with self.assertRaises(ValueError):
            out.notify_targets(0)

        with self.assertRaises(ValueError):
            out.get_data(0)

        out = Output(name="Out")
        with self.assertRaises(FinamMetaDataError):
            out.push_info(0)

        with self.assertRaises(FinamNoDataError):
            out.get_info(Info(grid=NoGrid()))

        out.push_info(Info(grid=None, units=None))
        with self.assertRaises(FinamMetaDataError):
            out.get_info(Info(grid=None))

        with self.assertRaises(FinamMetaDataError):
            out.get_info(Info(grid=NoGrid()))

        with self.assertRaises(FinamMetaDataError):
            out.get_info(Info(grid=NoGrid(), units=None))

    def test_callback_input_fail(self):
        inp = CallbackInput(callback=lambda t: t, name="In")

        with self.assertRaises(ValueError):
            inp.source_changed(0)


class NotImplComponent(ATimeComponent):
    def __init__(self):
        super().__init__()
        self._time = datetime(2000, 1, 1)


class NotImplAdapter(AAdapter):
    def __init__(self):
        super().__init__()


class TestNotImplemented(unittest.TestCase):
    def test_comp_not_implemented(self):
        comp = NotImplComponent()

        with self.assertRaises(NotImplementedError):
            comp.initialize()
        with self.assertRaises(NotImplementedError):
            comp._initialize()

        with self.assertRaises(NotImplementedError):
            comp.connect()
        with self.assertRaises(NotImplementedError):
            comp._connect()

        with self.assertRaises(NotImplementedError):
            comp.validate()
        with self.assertRaises(NotImplementedError):
            comp._validate()

        with self.assertRaises(NotImplementedError):
            comp.update()
        with self.assertRaises(NotImplementedError):
            comp._update()

        with self.assertRaises(NotImplementedError):
            comp.finalize()
        with self.assertRaises(NotImplementedError):
            comp._finalize()

    def test_adapter_not_implemented(self):
        adapter = NotImplAdapter()
        with self.assertRaises(NotImplementedError):
            adapter.get_data(datetime(2000, 1, 1))
        with self.assertRaises(NotImplementedError):
            adapter._get_data(datetime(2000, 1, 1))


if __name__ == "__main__":
    unittest.main()
