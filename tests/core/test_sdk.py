"""
Unit tests for the sdk implementations.
"""
import logging
import unittest
from datetime import datetime, timedelta

import finam as fm
from finam import (
    Adapter,
    CallbackInput,
    CallbackOutput,
    ComponentStatus,
    Composition,
    FinamDataError,
    FinamLogError,
    FinamMetaDataError,
    FinamNoDataError,
    FinamStatusError,
    FinamTimeError,
    Info,
    Input,
    NoGrid,
    Output,
    TimeComponent,
)
from finam.sdk.component import IOList


class MockupAdapter(Adapter):
    def __init__(self):
        super().__init__()

    def _get_data(self, time):
        return time


class MockupComponent(TimeComponent):
    def __init__(self):
        super().__init__()
        self._time = datetime(2000, 1, 1)

    @property
    def next_time(self):
        return self.time + timedelta(days=1)

    def _initialize(self):
        self.status = ComponentStatus.FAILED


class MockupComponentIO(TimeComponent):
    def __init__(self):
        super().__init__()
        self._time = datetime(2000, 1, 1)

    @property
    def next_time(self):
        return self.time + timedelta(days=1)

    def _initialize(self):
        self.inputs.add(name="Input")
        self.outputs.add(name="Output")


class MockupComponentIONameConflict(TimeComponent):
    def __init__(self):
        super().__init__()
        self._time = datetime(2000, 1, 1)

    @property
    def next_time(self):
        return self.time + timedelta(days=1)

    def _initialize(self):
        self.inputs.add(name="IO")
        self.outputs.add(name="IO")


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

    def test_simple_io_access(self):
        comp_ok = MockupComponentIO()
        comp_fail = MockupComponentIONameConflict()

        comp_ok.initialize()
        comp_fail.initialize()

        inp = comp_ok["Input"]
        out = comp_ok["Output"]

        self.assertTrue(isinstance(inp, fm.IInput))
        self.assertTrue(isinstance(out, fm.IOutput))

        with self.assertRaises(KeyError):
            _inp = comp_ok["abc"]

        with self.assertRaises(KeyError):
            _inp = comp_fail["IO"]

    def test_simple_io_not_initialized(self):
        comp_ok = MockupComponentIO()

        with self.assertRaises(KeyError):
            _inp = comp_ok["Input"]
        with self.assertRaises(KeyError):
            _inp = comp_ok["Output"]


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
        info = Info(time=t, grid=NoGrid(), meta={"test": 0})
        wrong_info = Info(time=t, grid=NoGrid(), meta={"test": 5})

        def callback(_clr, _time):
            nonlocal counter
            counter += 1

        out = Output(name="Output")
        inp = CallbackInput(callback=callback, name="Callback")

        out >> inp

        with self.assertRaises(FinamNoDataError):
            out.get_data(t, None)

        out.push_info(info)
        out._connected_inputs = {inp: None}

        with self.assertRaises(FinamNoDataError):
            out.push_data(100, t)

        self._out_infos_exchanged = 1

        out.get_info(info)

        with self.assertRaises(FinamMetaDataError):
            out.get_info(wrong_info)

        out._output_info.time = None
        with self.assertRaises(FinamMetaDataError):
            out.get_info(Info(time=None, grid=NoGrid()))

        out._output_info.time = t

        out.push_data(100, t)

        self.assertTrue(inp.has_source)
        self.assertTrue(out.has_targets)
        self.assertEqual(out.get_info(info), info)
        self.assertEqual(out.get_data(t, None), 100)
        self.assertEqual(inp.exchange_info(info), info)
        self.assertEqual(inp.pull_data(t), 100)
        self.assertEqual(counter, 1)

    def test_know_targets(self):
        out = Output(name="Output")
        in1 = Input(name="In1")
        in2 = Input(name="In1")

        ada = fm.adapters.Scale(2.0)

        out >> ada
        ada >> in1
        ada >> in2

        in1.ping()
        in2.ping()

        self.assertEqual(out._connected_inputs, {in1: None, in2: None})

        with self.assertRaises(ValueError):
            in1.ping()

    def test_know_targets_adapter(self):
        out = Output(name="Output")
        in1 = Input(name="In1")
        in2 = Input(name="In1")

        ada = fm.adapters.LinearTime()

        out >> ada
        ada >> in1
        ada >> in2

        in1.ping()
        in2.ping()

        self.assertEqual(out._connected_inputs, {ada: None})

    def test_cache_data(self):
        t = datetime(2000, 1, 1)
        info = Info(time=t, grid=NoGrid())

        out = Output(name="Output")
        inp = Input(name="Input")

        out >> inp

        inp.ping()

        out.push_info(info)
        inp.exchange_info(info)

        self.assertEqual(out._connected_inputs, {inp: None})

        out.push_data(1, t)
        self.assertEqual(out.data, [(t, 1)])

        with self.assertRaises(FinamTimeError):
            data = inp.pull_data(t - timedelta(hours=1))
        with self.assertRaises(FinamTimeError):
            data = inp.pull_data(t + timedelta(hours=1))

        data = inp.pull_data(t)
        self.assertEqual(out.data, [(t, 1)])
        self.assertEqual(data, 1)

        t2 = t + timedelta(days=1)
        out.push_data(2, t2)
        self.assertEqual(out.data, [(t, 1), (t2, 2)])

        with self.assertRaises(FinamTimeError):
            data = inp.pull_data(t - timedelta(hours=1))
        with self.assertRaises(FinamTimeError):
            data = inp.pull_data(t2 + timedelta(hours=1))

        self.assertEqual(inp.pull_data(t), 1)
        self.assertEqual(inp.pull_data(t + timedelta(hours=0)), 1)
        self.assertEqual(inp.pull_data(t + timedelta(hours=11)), 1)
        self.assertEqual(inp.pull_data(t + timedelta(hours=12)), 2)

        self.assertEqual(len(out.data), 2)
        self.assertEqual(inp.pull_data(t2), 2)
        self.assertEqual(len(out.data), 1)

        out.push_data(3, t + timedelta(days=2))
        out.push_data(4, t + timedelta(days=3))
        out.push_data(5, t + timedelta(days=4))

        self.assertEqual(len(out.data), 4)
        self.assertEqual(inp.pull_data(t + timedelta(days=2)), 3)
        self.assertEqual(len(out.data), 3)

    def test_cache_data_multi(self):
        t = datetime(2000, 1, 1)
        info = Info(time=t, grid=NoGrid())

        out = Output(name="Output")
        in1 = Input(name="Input")
        in2 = Input(name="Input")

        out >> in1
        out >> in2

        in1.ping()
        in2.ping()

        out.push_info(info)
        in1.exchange_info(info)
        in2.exchange_info(info)

        for i in range(10):
            out.push_data(i + 1, t + timedelta(days=i))

        self.assertEqual(len(out.data), 10)

        in1.pull_data(datetime(2000, 1, 3))
        self.assertEqual(len(out.data), 10)

        in2.pull_data(datetime(2000, 1, 1))
        self.assertEqual(len(out.data), 10)

        in2.pull_data(datetime(2000, 1, 2))
        self.assertEqual(len(out.data), 9)

        in2.pull_data(datetime(2000, 1, 8))
        self.assertEqual(len(out.data), 8)

        in1.pull_data(datetime(2000, 1, 8))
        self.assertEqual(len(out.data), 3)

        in1.pull_data(datetime(2000, 1, 10))
        self.assertEqual(len(out.data), 3)
        in2.pull_data(datetime(2000, 1, 10))
        self.assertEqual(len(out.data), 1)

    def test_push_static(self):
        t = datetime(2000, 1, 1)
        info = Info(time=t, grid=NoGrid())

        out = Output(name="Output", static=True)
        in1 = Input(name="Input")

        out >> in1

        in1.ping()

        out.push_info(info)
        in1.exchange_info(info)

        out.push_data(0, None)

        with self.assertRaises(FinamDataError):
            out.push_data(0, None)


class TestInput(unittest.TestCase):
    def test_fail_set_source(self):
        time = datetime(2000, 1, 1)
        inp = Input(name="In", time=time, grid=NoGrid())
        outp = Output(name="Out", time=time, grid=NoGrid())

        with self.assertRaises(ValueError):
            inp.set_source(0)

        inp.set_source(outp)

        with self.assertRaises(ValueError):
            inp.set_source(outp)

    def test_pull_static(self):
        t = datetime(2000, 1, 1)
        info = Info(time=t, grid=NoGrid())

        out = Output(name="Output", static=True)
        in1 = Input(name="Input", static=True)

        out >> in1

        in1.ping()

        out.push_info(info)
        in1.exchange_info(info)

        out.push_data(0, None)
        data = in1.pull_data(None)

        self.assertFalse(fm.data.has_time_axis(data))

        with self.assertRaises(FinamDataError):
            in1.pull_data(None)

    def test_pull_dynamic_time(self):
        t = datetime(2000, 1, 1)
        info = Info(time=t, grid=NoGrid())

        out = Output(name="Output", static=True)
        in1 = Input(name="Input")

        out >> in1

        in1.ping()

        out.push_info(info)
        in1.exchange_info(info)

        out.push_data(0, None)
        data = in1.pull_data(t)

        self.assertTrue(fm.data.has_time_axis(data))
        self.assertEqual(fm.data.get_time(data)[0], t)


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
        out = Output(name="Out")

        out >> inp

        inp.source_updated(t)

        self.assertEqual(caller, inp)
        self.assertEqual(counter, 1)


class TestCallbackOutput(unittest.TestCase):
    def test_callback_output(self):
        caller = None
        counter = 0
        t = datetime(2000, 1, 1)

        def callback(clr, _time):
            nonlocal caller
            nonlocal counter
            caller = clr
            counter += 1
            return 42 if counter == 1 else None

        out = CallbackOutput(callback=callback, name="callback")
        inp = Input(name="input", time=t, grid=NoGrid())

        out >> inp
        inp.ping()

        with self.assertRaises(NotImplementedError):
            _data = out.push_data(0, t)

        with self.assertRaises(ValueError):
            _data = out.get_data(0, None)

        with self.assertRaises(FinamNoDataError):
            _data = out.get_data(t, None)

        out._output_info = Info(time=t, grid=NoGrid())

        with self.assertRaises(FinamNoDataError):
            _data = out.get_data(t, None)

        out._out_infos_exchanged = 1

        data = out.get_data(t, None)

        self.assertEqual(data, 42)
        self.assertEqual(caller, out)
        self.assertEqual(counter, 1)

        with self.assertRaises(FinamNoDataError):
            _data = out.get_data(t, None)


class TestIOList(unittest.TestCase):
    def test_io_list(self):
        inp = Input("test1")
        out = Output("test2")
        inp_list = IOList(None, "INPUT")
        out_list = IOList(None, "OUTPUT")

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

    def test_io_list_fail(self):
        comp = MockupComponent()
        inp_list = IOList(None, "INPUT")

        with self.assertRaises(KeyError):
            inp_list["In"]

        inp_list.owner = comp
        with self.assertRaises(KeyError):
            inp_list["In"]

        comp.initialize()
        with self.assertRaises(KeyError):
            inp_list["In"]


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

    def test_get_slot_fail(self):
        comp = MockupComponentIONameConflict()
        comp.initialize()

        with self.assertRaises(KeyError):
            _ = comp["IO"]

        comp = MockupComponentIO()

        with self.assertRaises(KeyError):
            _ = comp["Input"]

        with self.assertRaises(KeyError):
            _ = comp["Output"]

        comp.initialize()
        _ = comp["Input"]
        _ = comp["Output"]

        with self.assertRaises(KeyError):
            _ = comp["x"]

        with self.assertRaises(KeyError):
            _ = comp["x"]


class TestAdapter(unittest.TestCase):
    def test_adapter(self):
        adapter = MockupAdapter()
        adapter.push_data(1, datetime(2000, 1, 1))

        with self.assertRaises(ValueError):
            adapter.push_data(1, 0)

        with self.assertRaises(ValueError):
            adapter.source_updated(0)

        with self.assertRaises(FinamMetaDataError):
            adapter.exchange_info(None)

        with self.assertRaises(FinamMetaDataError):
            adapter.exchange_info(0)

        with self.assertRaises(FinamLogError):
            adapter.set_source(0)

        self.assertEqual(adapter.info, None)

    def test_adapter_static(self):
        adapter = MockupAdapter()
        self.assertFalse(adapter.is_static)


class TestIOFails(unittest.TestCase):
    def test_input_output_fail(self):
        t = datetime(2000, 1, 1)

        with self.assertRaises(ValueError):
            _in = Input(name=None)
        with self.assertRaises(ValueError):
            _in = Input(name="In", info=Info(time=t, grid=NoGrid()), units="m")

        with self.assertRaises(ValueError):
            _in = Output(name=None)
        with self.assertRaises(ValueError):
            _in = Output(name="In", info=Info(time=t, grid=NoGrid()), units="m")

        inp = Input(name="In", time=t, grid=NoGrid())
        out = Output(name="Out", time=t, grid=NoGrid())
        out >> inp
        with self.assertRaises(ValueError):
            inp.pull_data(0)

        inp = Input(name="In", time=t, grid=NoGrid())
        out = Output(name="Out", time=t, grid=NoGrid())
        out >> inp
        inp._in_info_exchanged = True
        with self.assertRaises(FinamMetaDataError):
            inp.exchange_info(info=Info(time=t, grid=NoGrid()))

        inp = Input(name="In")
        out = Output(name="Out", time=t, grid=NoGrid())
        out >> inp
        with self.assertRaises(FinamMetaDataError):
            inp.exchange_info(info=None)

        inp = Input(name="In", time=t, grid=NoGrid())
        out = Output(name="Out", time=t, grid=NoGrid())
        out >> inp
        with self.assertRaises(FinamMetaDataError):
            inp.exchange_info(info=Info(time=t, grid=NoGrid()))

        inp = Input(name="In")
        out = Output(name="Out", time=t, grid=NoGrid())
        out >> inp
        with self.assertRaises(FinamMetaDataError):
            inp.exchange_info(info=100)

        out = Output(name="Out", time=t, grid=NoGrid())
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
            out.get_data(0, None)

        out = Output(name="Out")
        with self.assertRaises(FinamMetaDataError):
            out.push_info(0)

        with self.assertRaises(FinamNoDataError):
            out.get_info(Info(time=t, grid=NoGrid()))

        out.push_info(Info(time=t, grid=None, units=None))
        with self.assertRaises(FinamMetaDataError):
            out.get_info(Info(time=t, grid=None))

        with self.assertRaises(FinamMetaDataError):
            out.get_info(Info(time=t, grid=NoGrid()))

        with self.assertRaises(FinamMetaDataError):
            out.get_info(Info(time=t, grid=NoGrid(), units=None))

    def test_callback_input_fail(self):
        inp = CallbackInput(callback=lambda t: t, name="In")
        out = Output(name="Out")

        out >> inp

        with self.assertRaises(ValueError):
            inp.source_updated(0)


class NotImplComponent(TimeComponent):
    def __init__(self):
        super().__init__()
        self._time = datetime(2000, 1, 1)

    @property
    def next_time(self):
        return self.time + timedelta(days=1)


class NotImplAdapter(Adapter):
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

        # check that the debug log for not implementing _validate is there
        with self.assertLogs(level=logging.DEBUG) as captured:
            comp.validate()
        self.assertEqual(len(captured.records), 2)
        self.assertEqual(captured.records[0].levelno, logging.DEBUG)
        self.assertEqual(captured.records[1].levelno, logging.DEBUG)
        with self.assertLogs(level=logging.DEBUG) as captured:
            comp._validate()
        self.assertEqual(len(captured.records), 1)
        self.assertEqual(captured.records[0].levelno, logging.DEBUG)

        with self.assertRaises(NotImplementedError):
            comp.update()
        with self.assertRaises(NotImplementedError):
            comp._update()

        # check that the debug log for not implementing _finalize is there
        with self.assertLogs(level=logging.DEBUG) as captured:
            comp.finalize()
        self.assertEqual(len(captured.records), 2)
        self.assertEqual(captured.records[0].levelno, logging.DEBUG)
        self.assertEqual(captured.records[1].levelno, logging.DEBUG)
        with self.assertLogs(level=logging.DEBUG) as captured:
            comp._finalize()
        self.assertEqual(len(captured.records), 1)
        self.assertEqual(captured.records[0].levelno, logging.DEBUG)

    def test_adapter_not_implemented(self):
        adapter = NotImplAdapter()
        with self.assertRaises(NotImplementedError):
            adapter.get_data(datetime(2000, 1, 1), None)
        with self.assertRaises(NotImplementedError):
            adapter._get_data(datetime(2000, 1, 1), None)


if __name__ == "__main__":
    unittest.main()
