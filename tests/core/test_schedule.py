"""
Unit tests for the driver/scheduler.
"""
import logging
import os
import unittest
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

import finam as fm
from finam import (
    Adapter,
    CallbackInput,
    CallbackOutput,
    Component,
    ComponentStatus,
    Composition,
    FinamConnectError,
    FinamStatusError,
    Info,
    Input,
    NoBranchAdapter,
    NoGrid,
    Output,
    TimeComponent,
)
from finam import data as tools
from finam.adapters.base import Scale
from finam.adapters.time import NextTime
from finam.modules import CallbackComponent, CallbackGenerator, debug
from finam.schedule import _check_dead_links


class NoTimeComponent(Component):
    def __init__(self):
        super().__init__()

    def _initialize(self):
        self.create_connector()

    def _connect(self):
        self.try_connect()

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

    @property
    def next_time(self):
        return self.time + self._step

    def _initialize(self):
        self.create_connector()

    def _connect(self):
        push_data = {}
        for key, callback in self._callbacks.items():
            push_data[key] = callback(self._time)

        self.try_connect(push_data=push_data)

    def _validate(self):
        pass

    def _update(self):
        self._time += self._step

        for key, callback in self._callbacks.items():
            self.outputs[key].push_data(callback(self._time), self.time)

    def _finalize(self):
        pass


class MockupDependentComponent(TimeComponent):
    def __init__(self, step):
        super().__init__()
        self._step = step
        self._time = datetime(2000, 1, 1)

        self.inputs.add(name="Input")

    @property
    def next_time(self):
        return self.time + self._step

    def _initialize(self):
        self.create_connector(pull_data=["Input"])

    def _connect(self):
        self.try_connect(
            self.time, exchange_infos={"Input": Info(time=self.time, grid=NoGrid())}
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

    @property
    def next_time(self):
        return self.time + self._step

    def _initialize(self):
        self.inputs.add(name="Input")
        self.outputs.add(name="Output", time=self.time, grid=NoGrid())
        self.create_connector(pull_data=["Input"])

    def _connect(self):
        push_data = {}
        pulled_data = self.connector.in_data["Input"]
        if pulled_data is not None:
            push_data["Output"] = tools.get_data(tools.strip_time(pulled_data))

        self.try_connect(
            exchange_infos={"Input": Info(time=self.time, grid=NoGrid())},
            push_data=push_data,
        )

    def _validate(self):
        pass

    def _update(self):
        pulled = self.inputs["Input"].pull_data(self.time)
        self._time += self._step
        self.outputs["Output"].push_data(
            tools.get_data(tools.strip_time(pulled)), self.time
        )

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
        composition.initialize()

        self.assertEqual(module.status, ComponentStatus.INITIALIZED)
        self.assertEqual(len(module.outputs), 1)

    def test_check_composition(self):
        with self.assertRaises(ValueError):
            _comp = Composition(["not a component"])

    def test_validate_branching(self):
        module = MockupComponent(callbacks={"Output": lambda t: t}, step=timedelta(1.0))
        composition = Composition([module])
        composition.initialize()

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
        composition.initialize()

        with self.assertRaises(FinamConnectError) as context:
            composition._validate_composition()

        self.assertTrue("Unconnected input" in str(context.exception))

    def test_log_file(self):
        with TemporaryDirectory() as tmp:
            log_file = os.path.join(tmp, "test.log")

            module1 = MockupComponent(
                callbacks={"Output": lambda t: t}, step=timedelta(1.0)
            )
            module2 = MockupDependentComponent(step=timedelta(1.0))

            composition = Composition(
                [module2, module1], log_level=logging.DEBUG, log_file=log_file
            )
            composition.initialize()

            module1.outputs["Output"] >> module2.inputs["Input"]

            composition.run(t_max=datetime(2000, 1, 2))

            with open(log_file) as f:
                lines = f.readlines()
                self.assertNotEqual(len(lines), 0)

    def test_fail_time(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: t}, step=timedelta(1.0)
        )
        composition = Composition([module1])
        composition.initialize()

        with self.assertRaises(ValueError):
            composition.run(t_max=100)

    def test_fail_double_initialize(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: t}, step=timedelta(1.0)
        )
        composition = Composition([module1])
        composition.initialize()

        with self.assertRaises(FinamStatusError):
            composition.initialize()

    def test_fail_double_connect(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: t}, step=timedelta(1.0)
        )
        composition = Composition([module1])
        composition.initialize()
        composition.connect()

        with self.assertRaises(FinamStatusError):
            composition.connect()

    def test_base_logger(self):
        composition = Composition([])
        self.assertFalse(composition.uses_base_logger_name)

    def test_iterative_connect(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: t}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module2, module1])
        composition.initialize()

        module1.outputs["Output"] >> module2.inputs["Input"]

        composition.run(t_max=datetime(2000, 1, 31))

    def test_iterative_connect_multi(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: t}, step=timedelta(1.0)
        )
        module2 = MockupCircularComponent(step=timedelta(1.0))
        module3 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module3, module2, module1])
        composition.initialize()

        module1.outputs["Output"] >> module2.inputs["Input"]
        module2.outputs["Output"] >> module3.inputs["Input"]

        composition.run(t_max=datetime(2000, 1, 31))

    def test_iterative_connect_adapter(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module2, module1])
        composition.initialize()

        module1.outputs["Output"] >> Scale(1.0) >> module2.inputs["Input"]

        composition.run(t_max=datetime(2000, 1, 31))

    def test_iterative_connect_multi_adapter(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module2, module1])
        composition.initialize()

        module1.outputs["Output"] >> Scale(1.0) >> Scale(1.0) >> module2.inputs["Input"]

        composition.run(t_max=datetime(2000, 1, 31))

    def test_iterative_connect_blocked(self):
        module1 = MockupCircularComponent(step=timedelta(1.0))
        module2 = MockupCircularComponent(step=timedelta(1.0))

        composition = Composition([module1, module2])
        composition.initialize()

        module1.outputs["Output"] >> module2.inputs["Input"]
        module2.outputs["Output"] >> module1.inputs["Input"]

        with self.assertRaises(FinamStatusError):
            composition.run(t_max=datetime(2000, 1, 31))

    def test_no_time_comp(self):
        module = NoTimeComponent()

        composition = Composition([module])
        composition.initialize()

        with self.assertRaises(ValueError):
            composition.run(t_max=datetime(2000, 1, 31))

        composition.run(t_max=None)

    def test_time_comp(self):
        module = MockupComponent(callbacks={"Output": lambda t: t}, step=timedelta(1.0))

        composition = Composition([module])
        composition.initialize()

        with self.assertRaises(ValueError):
            composition.run(t_max=None)

        composition.run(t_max=datetime(2000, 1, 2))

    def test_no_update(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(days=1)
        )
        module2 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(days=31)
        )
        composition = Composition([module1, module2])
        composition.initialize()
        composition.run(t_max=datetime(2000, 1, 1))

    def test_missing_component_upstream(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module2])
        composition.initialize()

        module1.outputs["Output"] >> Scale(1.0) >> Scale(1.0) >> module2.inputs["Input"]

        with self.assertRaises(FinamConnectError):
            composition.connect()

    def test_missing_component_downstream(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module1])
        composition.initialize()

        module1.outputs["Output"] >> Scale(1.0) >> Scale(1.0) >> module2.inputs["Input"]

        with self.assertRaises(FinamConnectError):
            composition.connect()

    def test_dependencies_simple(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module1, module2])
        composition.initialize()

        module1.outputs["Output"] >> Scale(1.0) >> module2.inputs["Input"]

        composition.connect()

        self.assertEqual(composition.dependencies, {module1: set(), module2: {module1}})

    def test_dependencies_multi(self):
        module1 = MockupComponent(
            callbacks={"Output": lambda t: 1.0}, step=timedelta(1.0)
        )
        module2 = MockupDependentComponent(step=timedelta(1.0))

        module3 = MockupCircularComponent(step=timedelta(1.0))
        module4 = MockupDependentComponent(step=timedelta(1.0))

        composition = Composition([module1, module2, module3, module4])
        composition.initialize()

        module1.outputs["Output"] >> Scale(1.0) >> module2.inputs["Input"]
        module1.outputs["Output"] >> Scale(1.0) >> module3.inputs["Input"]
        module3.outputs["Output"] >> Scale(1.0) >> module4.inputs["Input"]

        composition.connect()

        self.assertEqual(
            composition.dependencies,
            {
                module1: set(),
                module2: {module1},
                module3: {module1},
                module4: {module3},
            },
        )

    def test_static_run(self):
        info = fm.Info(time=None, grid=fm.NoGrid())

        source = fm.modules.StaticSimplexNoise(info=info, seed=123)
        sink = fm.modules.DebugPushConsumer(
            inputs={
                "In": fm.Info(time=None, grid=fm.NoGrid()),
            },
        )

        composition = Composition([source, sink])
        composition.initialize()

        source.outputs["Noise"] >> Scale(1.0) >> sink.inputs["In"]

        with self.assertRaises(ValueError):
            composition.run(t_max=datetime(2000, 1, 1))

        composition.run()

        # We get data without the time dimension here
        self.assertEqual(sink.data["In"].shape, ())

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
        composition.initialize()

        module1.outputs["Out"] >> Scale(1.0) >> module2.inputs["In"]
        module2.outputs["Out"] >> Scale(1.0) >> module3.inputs["In"]

        composition.connect()
        self.assertEqual(updates, ["A", "B", "C"])

        composition.run(datetime(2000, 1, 2))
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


if __name__ == "__main__":
    unittest.main()
