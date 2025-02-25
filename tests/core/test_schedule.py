"""
Unit tests for the driver/scheduler.
"""

import logging
import os
import pprint
import unittest
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

import numpy as np

import finam as fm
from finam import (
    Adapter,
    CallbackInput,
    CallbackOutput,
    Component,
    ComponentStatus,
    Composition,
    FinamCircularCouplingError,
    FinamConnectError,
    FinamStatusError,
    Info,
    Input,
    NoBranchAdapter,
    NoGrid,
    Output,
    TimeComponent,
)
from finam._version import __version__
from finam.adapters.base import Scale
from finam.adapters.time import DelayFixed, NextTime
from finam.components import (
    CallbackComponent,
    CallbackGenerator,
    DebugPushConsumer,
    debug,
)
from finam.schedule import _check_dead_links, _find_dependencies


class NoTimeComponent(Component):
    def __init__(self):
        super().__init__()

    def _initialize(self):
        self.create_connector()

    def _connect(self, start_time):
        self.try_connect(start_time)

    def _validate(self):
        pass

    def _update(self):
        pass

    def _finalize(self):
        pass


class MockupComponent(TimeComponent):
    def __init__(self, callbacks, step):
        super().__init__()

        if not isinstance(step, timedelta):
            raise ValueError("Step must be of type timedelta")

        self._callbacks = callbacks
        self._step = step
        self._time = datetime(2000, 1, 1)

        for key, _ in self._callbacks.items():
            self.outputs.add(name=key, time=self.time, grid=NoGrid())

    def _next_time(self):
        return self.time + self._step

    def _initialize(self):
        self.create_connector()

    def _connect(self, start_time):
        push_data = {}
        for key, callback in self._callbacks.items():
            push_data[key] = callback(self._time)

        self.try_connect(start_time, push_data=push_data)

    def _validate(self):
        pass

    def _update(self):
        self._time += self._step

        for key, callback in self._callbacks.items():
            self.outputs[key].push_data(callback(self._time), self.time)

    def _finalize(self):
        pass


class MockupDependentComponent(TimeComponent):
    def __init__(self, step, static=False):
        super().__init__()
        self._step = step
        self._time = datetime(2000, 1, 1)
        self.static = static

        self.inputs.add(name="Input", static=self.static)

    def _next_time(self):
        return self.time + self._step

    def _initialize(self):
        self.create_connector(pull_data=["Input"])

    def _connect(self, start_time):
        self.try_connect(
            start_time, exchange_infos={"Input": Info(time=self.time, grid=NoGrid())}
        )

    def _validate(self):
        pass

    def _update(self):
        _pulled = self.inputs["Input"].pull_data(self.time)
        self._time += self._step

    def _finalize(self):
        pass


class MockupCircularComponent(TimeComponent):
    def __init__(self, step):
        super().__init__()
        self._step = step
        self._time = datetime(2000, 1, 1)

        self.pulled_data = None

    def _next_time(self):
        return self.time + self._step

    def _initialize(self):
        self.inputs.add(name="Input")
        self.outputs.add(name="Output", time=self.time, grid=NoGrid())
        self.create_connector(pull_data=["Input"])

    def _connect(self, start_time):
        push_data = {}
        pulled_data = self.connector.in_data["Input"]
        if pulled_data is not None:
            push_data["Output"] = pulled_data[0, ...]

        self.try_connect(
            start_time,
            exchange_infos={"Input": Info(time=self.time, grid=NoGrid())},
            push_data=push_data,
        )

    def _validate(self):
        pass

    def _update(self):
        self._time += self._step
        pulled = self.inputs["Input"].pull_data(self.time)
        self.outputs["Output"].push_data(pulled, self.time)

    def _finalize(self):
        pass


class CallbackAdapter(Adapter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def _get_data(self, time):
        return self.callback(self.pull_data(time), time)


class NbAdapter(Adapter, NoBranchAdapter):
    def _get_data(self, time):
        return self.pull_data(time)


class TestComposition(unittest.TestCase):
    def test_init(self):
        module = MockupComponent(callbacks={"Output": lambda t: t}, step=timedelta(1.0))
        composition = Composition([module])

        self.assertEqual(module.status, ComponentStatus.INITIALIZED)
        self.assertEqual(len(module.outputs), 1)

    def test_check_composition(self):
        with self.assertRaises(ValueError):
            _comp = Composition(["not a component"])

    def test_validate_branching(self):
        module = MockupComponent(callbacks={"Output": lambda t: t}, step=timedelta(1.0))
        composition = Composition([module])

        non_branching_adapter = (
            module.outputs["Output"]
            >> NbAdapter()
            >> CallbackAdapter(callback=lambda data, time: data)
        )

        non_branching_adapter >> CallbackAdapter(callback=lambda data, time: data)
        non_branching_adapter >> CallbackAdapter(callback=lambda data, time: data)

        with self.assertRaises(FinamConnectError) as context:
            composition._validate_composition()

        self.assertTrue("Disallowed branching" in str(context.exception))

    def test_check_dead_links(self):
        info = Info(time=None, grid=NoGrid())

        out = Output(name="out", info=info)
        inp = Input(name="in", info=info)
        out >> inp

        self.assertTrue(inp.needs_pull)
        self.assertFalse(inp.needs_push)
        self.assertFalse(out.needs_pull)
        self.assertTrue(out.needs_push)

        _check_dead_links(0, inp)

        out = CallbackOutput(name="out", callback=None, info=info)
        inp = CallbackInput(name="in", callback=None, info=info)
        out >> inp

        self.assertFalse(inp.needs_pull)
        self.assertTrue(inp.needs_push)
        self.assertTrue(out.needs_pull)
        self.assertFalse(out.needs_push)

        with self.assertRaises(FinamConnectError):
            _check_dead_links(0, inp)

        out = Output(name="out", info=info)
        ada = NextTime()
        inp = CallbackInput(name="in", callback=None, info=info)

        out >> ada >> inp
        _check_dead_links(0, inp)

        out = CallbackOutput(name="out", callback=None, info=info)
        ada = NextTime()
        inp = Input(name="in", info=info)

        out >> ada >> inp
        with self.assertRaises(FinamConnectError):
            _check_dead_links(0, inp)

    def test_check_dead_links_error(self):
        info = Info(time=None, grid=NoGrid())
        out = CallbackOutput(name="out", callback=None, info=info)
        ada1 = Scale(2.0)
        ada2 = Scale(2.0)
        inp = CallbackInput(name="in", callback=None, info=info)
        out >> ada1 >> ada2 >> inp

        with self.assertRaises(FinamConnectError) as context:
            _check_dead_links(0, inp)

        message = str(context.exception)
        self.assertTrue("out >/> Scale >> Scale >/> in" in message)

    def test_validate_inputs(self):
        time = datetime(2000, 1, 1)
        module = debug.DebugConsumer(
            {"Input": Info(time=time, grid=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        composition = Composition([module])

        with self.assertRaises(FinamConnectError) as context:
            composition._validate_composition()

        self.assertTrue("Unconnected input" in str(context.exception))

    def test_log_file(self):
        with TemporaryDirectory() as tmp:
            log_file = os.path.join(tmp, "test.log")

            module1 = MockupComponent(
                callbacks={"Output": lambda t: t.day}, step=timedelta(1.0)
            )
            module2 = MockupDependentComponent(step=timedelta(1.0))

            composition = Composition(
                [module2, module1], log_level=logging.DEBUG, log_file=log_file
            )

            module1.outputs["Output"] >> module2.inputs["Input"]

            composition.run(
                start_time=datetime(2000, 1, 1), end_time=datetime(2000, 1, 2)
            )

            with open(log_file) as f:
                lines = f.readlines()
                self.assertNotEqual(len(lines), 0)

    def test_collect_adapters(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: t.day}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module2, module1])

        ada = fm.adapters.Scale(1.0)
        module1.outputs["Output"] >> ada >> module2.inputs["Input"]

        composition.connect()

        self.assertEqual({ada}, composition._adapters)

    def test_fail_time(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: t}, step=timedelta(1.0)
        )
        composition = Composition([module1])

        with self.assertRaises(ValueError):
            composition.run(start_time=0, end_time=100)

    def test_fail_double_connect(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: t}, step=timedelta(1.0)
        )
        composition = Composition([module1])
        composition.connect(datetime(2000, 1, 1))

        with self.assertRaises(FinamStatusError):
            composition.connect(datetime(2000, 1, 1))

    def test_base_logger(self):
        composition = Composition([])
        self.assertFalse(composition.uses_base_logger_name)

    def test_iterative_connect(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: t.day}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module2, module1])

        module1.outputs["Output"] >> module2.inputs["Input"]

        composition.run(start_time=datetime(2000, 1, 1), end_time=datetime(2000, 1, 31))

    def test_iterative_connect_multi(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: t.day}, step=timedelta(1.0)
        )
        module2 = MockupCircularComponent(step=timedelta(1.0))
        module3 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module3, module2, module1])

        module1.outputs["Output"] >> module2.inputs["Input"]
        module2.outputs["Output"] >> module3.inputs["Input"]

        composition.run(start_time=datetime(2000, 1, 1), end_time=datetime(2000, 1, 31))

    def test_iterative_connect_adapter(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module2, module1])

        module1.outputs["Output"] >> Scale(1.0) >> module2.inputs["Input"]

        composition.run(start_time=datetime(2000, 1, 1), end_time=datetime(2000, 1, 31))

    def test_iterative_connect_multi_adapter(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module2, module1])

        module1.outputs["Output"] >> Scale(1.0) >> Scale(1.0) >> module2.inputs["Input"]

        composition.run(start_time=datetime(2000, 1, 1), end_time=datetime(2000, 1, 31))

    def test_iterative_connect_blocked(self):
        module1 = MockupCircularComponent(step=timedelta(1.0))
        module2 = MockupCircularComponent(step=timedelta(1.0))

        composition = Composition([module1, module2])

        module1.outputs["Output"] >> module2.inputs["Input"]
        module2.outputs["Output"] >> module1.inputs["Input"]

        with self.assertRaises(FinamCircularCouplingError):
            composition.run(
                start_time=datetime(2000, 1, 1), end_time=datetime(2000, 1, 31)
            )

    def test_no_time_comp(self):
        module = NoTimeComponent()

        composition = Composition([module])

        with self.assertRaises(ValueError):
            composition.run(end_time=datetime(2000, 1, 31))

        composition.run(end_time=None)

    def test_time_comp(self):
        module = MockupComponent(callbacks={"Output": lambda t: t}, step=timedelta(1.0))

        composition = Composition([module])

        with self.assertRaises(ValueError):
            composition.run(end_time=None)

        composition.run(start_time=datetime(2000, 1, 1), end_time=datetime(2000, 1, 2))

    def test_no_update(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(days=1)
        )
        module2 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(days=31)
        )
        composition = Composition([module1, module2])
        composition.run(start_time=datetime(2000, 1, 1), end_time=datetime(2000, 1, 1))

    def test_missing_component_upstream(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module2])

        module1.outputs["Output"] >> Scale(1.0) >> Scale(1.0) >> module2.inputs["Input"]

        with self.assertRaises(FinamConnectError):
            composition.connect(
                datetime(2000, 1, 1),
            )

    def test_missing_component_downstream(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module1])

        module1.outputs["Output"] >> Scale(1.0) >> Scale(1.0) >> module2.inputs["Input"]

        with self.assertRaises(FinamConnectError):
            composition.connect(datetime(2000, 1, 1))

    def test_dependencies_simple(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module1, module2])

        module1.outputs["Output"] >> Scale(1.0) >> module2.inputs["Input"]

        composition.connect(datetime(2000, 1, 1))

        self.assertEqual(
            _find_dependencies(
                module1, composition._output_owners, datetime(2000, 1, 5)
            ),
            {},
        )
        self.assertEqual(
            _find_dependencies(
                module2, composition._output_owners, datetime(2000, 1, 1)
            ),
            {},
        )
        self.assertEqual(
            _find_dependencies(
                module2, composition._output_owners, datetime(2000, 1, 5)
            ),
            {module1.outputs["Output"]: (datetime(2000, 1, 5), False)},
        )

    def test_dependencies_multi(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        module3 = MockupCircularComponent(step=timedelta(1.0))
        module4 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module1, module2, module3, module4])

        module1.outputs["Output"] >> Scale(1.0) >> module2.inputs["Input"]
        module1.outputs["Output"] >> Scale(1.0) >> module3.inputs["Input"]
        (
            module3.outputs["Output"]
            >> Scale(1.0)
            >> DelayFixed(timedelta(days=2))
            >> module4.inputs["Input"]
        )

        composition.connect(datetime(2000, 1, 1))

        self.assertEqual(
            _find_dependencies(
                module1, composition._output_owners, datetime(2000, 1, 5)
            ),
            {},
        )
        self.assertEqual(
            _find_dependencies(
                module2, composition._output_owners, datetime(2000, 1, 5)
            ),
            {module1.outputs["Output"]: (datetime(2000, 1, 5), False)},
        )
        self.assertEqual(
            _find_dependencies(
                module3, composition._output_owners, datetime(2000, 1, 5)
            ),
            {module1.outputs["Output"]: (datetime(2000, 1, 5), False)},
        )

        self.assertEqual(
            _find_dependencies(
                module4, composition._output_owners, datetime(2000, 1, 1)
            ),
            {},
        )
        self.assertEqual(
            _find_dependencies(
                module4, composition._output_owners, datetime(2000, 1, 2)
            ),
            {},
        )
        self.assertEqual(
            _find_dependencies(
                module4, composition._output_owners, datetime(2000, 1, 5)
            ),
            {module3.outputs["Output"]: (datetime(2000, 1, 3), True)},
        )

    def test_static_run(self):
        info = fm.Info(time=None, grid=fm.NoGrid())

        source = fm.components.StaticSimplexNoise(info=info, seed=123)
        sink = fm.components.DebugPushConsumer(
            inputs={
                "In": fm.Info(time=None, grid=fm.NoGrid()),
            },
        )

        composition = Composition([source, sink])

        source.outputs["Noise"] >> Scale(1.0) >> sink.inputs["In"]

        with self.assertRaises(ValueError):
            composition.run(end_time=datetime(2000, 1, 1))

        composition.run()

        # We get data without the time dimension here
        self.assertEqual(sink.data["In"].shape, (1,))

    def test_static_fail(self):
        info = fm.Info(time=None, grid=fm.NoGrid())

        source = fm.components.SimplexNoise(info=info, seed=123)
        sink = MockupDependentComponent(step=timedelta(days=1), static=True)

        composition = Composition([source, sink])

        source.outputs["Noise"] >> Scale(1.0) >> sink.inputs["Input"]

        with self.assertRaises(FinamConnectError):
            composition.connect(datetime(2000, 1, 1))

    def test_dependencies_schedule(self):
        start = datetime(2000, 1, 1)
        info = fm.Info(time=start, grid=fm.NoGrid())

        updates = []

        def lambda_generator(t):
            updates.append("A")
            return t.day

        def lambda_component(inp, _t):
            updates.append("B")
            return {"Out": inp["In"]}

        def lambda_component_2(inp, _t):
            updates.append("C")
            return {"Out": inp["In"]}

        module1 = CallbackGenerator(
            callbacks={"Out": (lambda_generator, info)},
            start=start,
            step=timedelta(1.0),
        )
        module2 = CallbackComponent(
            inputs={
                "In": fm.Info(time=None, grid=fm.NoGrid()),
            },
            outputs={
                "Out": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callback=lambda_component,
            start=start,
            step=timedelta(days=5),
        )
        module3 = CallbackComponent(
            inputs={
                "In": fm.Info(time=None, grid=fm.NoGrid()),
            },
            outputs={
                "Out": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callback=lambda_component_2,
            start=start,
            step=timedelta(days=8),
        )
        composition = Composition([module1, module2, module3])

        module1.outputs["Out"] >> Scale(1.0) >> module2.inputs["In"]
        module2.outputs["Out"] >> Scale(1.0) >> module3.inputs["In"]

        composition.connect(datetime(2000, 1, 1))
        self.assertEqual(updates, ["A", "B", "C"])

        composition.run(end_time=datetime(2000, 1, 2))
        self.assertEqual(
            updates,
            [
                "A",
                "B",
                "C",  # Connect
                "A",
                "A",
                "A",
                "A",
                "A",
                "B",  # Update B to 5
                "A",
                "A",
                "A",
                "A",
                "A",
                "B",  # Update B to 10
                "C",  # Update C to 8
            ],
        )

    def test_dependencies_schedule_no_push(self):
        start = datetime(2000, 1, 1)
        info = fm.Info(time=start, grid=fm.NoGrid())

        updates = []

        def lambda_generator(t):
            updates.append("A")
            if (t.day - 1) % 5 != 0:
                return None
            return t.day

        def lambda_component(inp, t):
            updates.append("B")
            return {"Out": inp["In"]}

        module1 = CallbackGenerator(
            callbacks={"Out": (lambda_generator, info)},
            start=start,
            step=timedelta(days=1),
        )
        module2 = CallbackComponent(
            inputs={
                "In": fm.Info(time=None, grid=fm.NoGrid()),
            },
            outputs={
                "Out": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callback=lambda_component,
            start=start,
            step=timedelta(days=1),
        )
        composition = Composition([module1, module2])

        module1.outputs["Out"] >> Scale(1.0) >> module2.inputs["In"]

        composition.connect()
        self.assertEqual(updates, ["A", "B"])

        composition.run(end_time=datetime(2000, 1, 2))
        self.assertEqual(
            updates,
            [
                "A",
                "B",  # Connect
                "A",
                "A",
                "A",
                "A",
                "A",
                "B",  # Update B to 5
            ],
        )

    def test_dependencies_schedule_no_push_double(self):
        start = datetime(2000, 1, 1)
        info = fm.Info(time=start, grid=fm.NoGrid())

        updates = []

        def lambda_generator_1(t):
            updates.append("A1")
            return t.day

        def lambda_generator_2(t):
            if (t.day - 1) % 5 != 0:
                return None
            updates.append("A2")
            return t.day

        def lambda_component(inp, t):
            updates.append("B")
            return {"Out": inp["In1"]}

        module1 = CallbackGenerator(
            callbacks={
                "Out1": (lambda_generator_1, info),
                "Out2": (lambda_generator_2, info),
            },
            start=start,
            step=timedelta(days=1),
        )
        module2 = CallbackComponent(
            inputs={
                "In1": fm.Info(time=None, grid=fm.NoGrid()),
                "In2": fm.Info(time=None, grid=fm.NoGrid()),
            },
            outputs={
                "Out": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callback=lambda_component,
            start=start,
            step=timedelta(days=1),
        )
        composition = Composition([module1, module2])

        module1.outputs["Out1"] >> Scale(1.0) >> module2.inputs["In1"]
        module1.outputs["Out2"] >> Scale(1.0) >> module2.inputs["In2"]

        composition.connect()
        self.assertEqual(updates, ["A1", "A2", "B"])

        composition.run(end_time=datetime(2000, 1, 2))
        self.assertEqual(
            updates,
            [
                "A1",
                "A2",
                "B",  # Connect
                "A1",
                "A1",
                "A1",
                "A1",
                "A1",
                "A2",
                "B",  # Update B to 5
            ],
        )

    def test_dependency_fail(self):
        start = datetime(2000, 1, 1)
        info = fm.Info(time=start, grid=fm.NoGrid())

        updates = []

        def lambda_component(inp, _t):
            return {"Out": inp["In"] if inp else 0.0}

        module1 = CallbackComponent(
            inputs={"In": info},
            outputs={"Out": info},
            callback=lambda_component,
            start=start,
            step=timedelta(days=5),
        )
        module2 = CallbackComponent(
            inputs={"In": info},
            outputs={"Out": info},
            callback=lambda_component,
            start=start,
            step=timedelta(days=8),
            initial_pull=False,
        )
        composition = Composition([module1, module2])

        module1.outputs["Out"] >> Scale(1.0) >> module2.inputs["In"]
        module2.outputs["Out"] >> Scale(1.0) >> module1.inputs["In"]

        composition.connect(start)

        with self.assertRaises(FinamCircularCouplingError):
            composition.run(end_time=datetime(2000, 1, 2))

    def test_starting_time(self):
        start_1 = datetime(2000, 1, 1)
        start_2 = datetime(2000, 1, 8)

        updates = {"A": [], "B": []}

        def lambda_generator(t):
            return t.day

        def lambda_component(inp, t):
            return {"Out": inp["In"][0, ...]}

        def lambda_debugger(name, data, t):
            updates[name].append(t.day)

        module1 = CallbackGenerator(
            callbacks={"Out": (lambda_generator, fm.Info(time=None, grid=fm.NoGrid()))},
            start=start_2,
            step=timedelta(days=5),
        )
        module2 = CallbackComponent(
            inputs={
                "In": fm.Info(time=None, grid=fm.NoGrid()),
            },
            outputs={
                "Out": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callback=lambda_component,
            start=start_1,
            step=timedelta(days=3),
        )
        module3 = DebugPushConsumer(
            inputs={
                "A": fm.Info(time=None, grid=None),
                "B": fm.Info(time=None, grid=None),
            },
            callbacks={
                "A": lambda_debugger,
                "B": lambda_debugger,
            },
        )

        composition = Composition([module1, module2, module3])

        module1.outputs["Out"] >> Scale(1.0) >> module2.inputs["In"]
        module1.outputs["Out"] >> Scale(1.0) >> module3.inputs["A"]
        module2.outputs["Out"] >> Scale(1.0) >> module3.inputs["B"]

        composition.connect()

        composition.run(end_time=datetime(2000, 1, 10))

        self.assertEqual([1, 8, 13], updates["A"])
        self.assertEqual([1, 4, 7, 10], updates["B"])

    def test_starting_time(self):
        start_1 = datetime(2000, 1, 2)
        start_2 = datetime(2000, 1, 8)

        updates = {"A": [], "B": []}

        def lambda_generator(t):
            return t.day

        def lambda_component(inp, t):
            return {"Out": inp["In"].copy()}

        def lambda_debugger(name, data, t):
            updates[name].append(t.day)

        module1 = CallbackGenerator(
            callbacks={"Out": (lambda_generator, fm.Info(time=None, grid=fm.NoGrid()))},
            start=start_2,
            step=timedelta(days=5),
        )
        module2 = CallbackComponent(
            inputs={
                "In": fm.Info(time=None, grid=fm.NoGrid()),
            },
            outputs={
                "Out": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callback=lambda_component,
            start=start_1,
            step=timedelta(days=3),
        )
        module3 = DebugPushConsumer(
            inputs={
                "A": fm.Info(time=None, grid=None),
                "B": fm.Info(time=None, grid=None),
            },
            callbacks={
                "A": lambda_debugger,
                "B": lambda_debugger,
            },
        )

        composition = Composition([module1, module2, module3])

        module1.outputs["Out"] >> Scale(1.0) >> module2.inputs["In"]
        module1.outputs["Out"] >> Scale(1.0) >> module3.inputs["A"]
        module2.outputs["Out"] >> Scale(1.0) >> module3.inputs["B"]

        composition.connect(datetime(2000, 1, 1))

        composition.run(end_time=datetime(2000, 1, 10))

        self.assertEqual([1, 8, 13], updates["A"])
        self.assertEqual([1, 2, 5, 8, 11], updates["B"])

    def test_metadata(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: t.day}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))
        module3 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module2, module1, module3])

        ada1 = fm.adapters.Scale(1.0)
        ada2 = fm.adapters.Scale(1.0)
        module1.outputs["Output"] >> ada1 >> ada2 >> module2.inputs["Input"]
        module1.outputs["Output"] >> module3.inputs["Input"]

        with self.assertRaises(FinamStatusError) as context:
            _ = composition.metadata

        composition.connect()

        md = composition.metadata

        pprint.pprint(md)

        self.assertIn("components", md)
        self.assertIn("adapters", md)
        self.assertIn("links", md)

        self.assertEqual([datetime(2000, 1, 1), None], md["time_frame"])

        self.assertIn(f"{module1.name}@{id(module1)}", md["components"])
        self.assertIn(f"{module2.name}@{id(module2)}", md["components"])
        self.assertIn(f"{ada1.name}@{id(ada1)}", md["adapters"])
        self.assertIn(f"{ada2.name}@{id(ada2)}", md["adapters"])

        self.assertEqual(4, len(md["links"]))
        self.assertTrue(
            {
                "from": {
                    "component": f"{module1.name}@{id(module1)}",
                    "output": "Output",
                },
                "to": {"component": f"{module3.name}@{id(module3)}", "input": "Input"},
            }
            in md["links"]
        )
        self.assertTrue(
            {
                "from": {
                    "component": f"{module1.name}@{id(module1)}",
                    "output": "Output",
                },
                "to": {"adapter": f"{ada1.name}@{id(ada1)}"},
            }
            in md["links"]
        )
        self.assertTrue(
            {
                "from": {"adapter": f"{ada1.name}@{id(ada1)}"},
                "to": {"adapter": f"{ada2.name}@{id(ada2)}"},
            }
            in md["links"]
        )
        self.assertTrue(
            {
                "from": {"adapter": f"{ada2.name}@{id(ada2)}"},
                "to": {"component": f"{module2.name}@{id(module2)}", "input": "Input"},
            }
            in md["links"]
        )

        self.assertEqual(__version__, md["version"])


if __name__ == "__main__":
    unittest.main()
