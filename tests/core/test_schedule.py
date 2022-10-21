"""
Unit tests for the driver/scheduler.
"""
import logging
import os
import unittest
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

from finam import (
    Adapter,
    Component,
    ComponentStatus,
    Composition,
    FinamStatusError,
    Info,
    NoBranchAdapter,
    NoGrid,
    TimeComponent,
)
from finam import data as tools
from finam.adapters.base import Scale
from finam.modules import debug


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

    def _initialize(self):
        for key, _ in self._callbacks.items():
            self.outputs.add(name=key, time=self.time, grid=NoGrid())
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

    def _initialize(self):
        self.inputs.add(name="Input")
        self.create_connector(required_in_data=["Input"])

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

    def _initialize(self):
        self.inputs.add(name="Input")
        self.outputs.add(name="Output", time=self.time, grid=NoGrid())
        self.create_connector(required_in_data=["Input"])

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

        with self.assertRaises(ValueError) as context:
            composition._validate()

        self.assertTrue("Disallowed branching" in str(context.exception))

    def test_validate_inputs(self):
        time = datetime(2000, 1, 1)
        module = debug.DebugConsumer(
            {"Input": Info(time=time, grid=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        composition = Composition([module])
        composition.initialize()

        with self.assertRaises(ValueError) as context:
            composition._validate()

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

        composition.run(t_max=datetime(2000, 1, 31))

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


if __name__ == "__main__":
    unittest.main()
