"""
Unit tests for the driver/scheduler.
"""

import unittest
from datetime import datetime, timedelta

from finam.adapters.base import Scale
from finam.core.interfaces import ComponentStatus, FinamStatusError, NoBranchAdapter
from finam.core.schedule import Composition
from finam.core.sdk import AAdapter, ATimeComponent, Input, Output
from finam.data import Info, NoGrid
from finam.tools.connect_helper import ConnectHelper


class MockupComponent(ATimeComponent):
    def __init__(self, callbacks, step):
        super().__init__()

        if not isinstance(step, timedelta):
            raise ValueError("Step must be of type timedelta")

        self._callbacks = callbacks
        self._step = step
        self._time = datetime(2000, 1, 1)
        self.status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()
        for key, _ in self._callbacks.items():
            self.outputs.add(name=key, info=Info(grid=NoGrid))

        self.status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()
        for key, callback in self._callbacks.items():
            self.outputs[key].push_data(callback(self._time), self.time)

        self.status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()
        self.status = ComponentStatus.VALIDATED

    def update(self):
        super().update()
        self._time += self._step

        for key, callback in self._callbacks.items():
            self.outputs[key].push_data(callback(self._time), self.time)

        self.status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()
        self.status = ComponentStatus.FINALIZED


class MockupDependentComponent(ATimeComponent):
    def __init__(self, step):
        super().__init__()
        self._step = step
        self._time = datetime(2000, 1, 1)
        self.status = ComponentStatus.CREATED

        self.connector = None

    def initialize(self):
        super().initialize()
        self.inputs.add(name="Input")
        self.connector = ConnectHelper(
            self.inputs, self.outputs, required_in_data=["Input"]
        )
        self.status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        self.status = self.connector.connect(
            self.time, exchange_infos={"Input": Info(grid=NoGrid)}
        )

    def validate(self):
        super().validate()
        self.status = ComponentStatus.VALIDATED

    def update(self):
        super().update()
        _pulled = self.inputs["Input"].pull_data(self.time)
        self._time += self._step
        self.status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()
        self.status = ComponentStatus.FINALIZED


class MockupCircularComponent(ATimeComponent):
    def __init__(self, step):
        super().__init__()
        self._step = step
        self._time = datetime(2000, 1, 1)
        self.status = ComponentStatus.CREATED

        self.pulled_data = None
        self.connector = None

    def initialize(self):
        super().initialize()
        self.inputs.add(name="Input")
        self.outputs.add(name="Output", info=Info(grid=NoGrid))
        self.connector = ConnectHelper(
            self.inputs, self.outputs, required_in_data=["Input"]
        )
        self.status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        push_data = {}
        pulled_data = self.connector.in_data["Input"]
        if pulled_data is not None:
            push_data["Output"] = pulled_data

        self.status = self.connector.connect(
            self.time, exchange_infos={"Input": Info(grid=NoGrid)}, push_data=push_data
        )

    def validate(self):
        super().validate()
        self.status = ComponentStatus.VALIDATED

    def update(self):
        super().update()
        pulled = self.inputs["Input"].pull_data(self.time)
        self._time += self._step
        self.outputs["Output"].push_data(pulled, self.time)

        self.status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()
        self.status = ComponentStatus.FINALIZED


class MockupConsumerComponent(ATimeComponent):
    def __init__(self):
        super().__init__()
        self.status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()
        self.inputs.add(name="Input")
        self.status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()
        self.inputs["Input"].exchange_info(Info(grid=NoGrid))


class CallbackAdapter(AAdapter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def get_data(self, time):
        return self.callback(self.pull_data(time), time)


class NbAdapter(AAdapter, NoBranchAdapter):
    def get_data(self, time):
        return self.pull_data(time)


class TestComposition(unittest.TestCase):
    def test_init_run(self):
        module = MockupComponent(callbacks={"Output": lambda t: t}, step=timedelta(1.0))
        composition = Composition([module])
        composition.initialize()

        self.assertEqual(module.status, ComponentStatus.INITIALIZED)
        self.assertEqual(len(module.outputs), 1)

        composition.run(t_max=datetime(2000, 1, 31))

        self.assertEqual(module.status, ComponentStatus.FINALIZED)
        self.assertEqual(module.time, datetime(2000, 1, 31))

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
        module = MockupConsumerComponent()
        composition = Composition([module])
        composition.initialize()

        with self.assertRaises(ValueError) as context:
            composition._validate()

        self.assertTrue("Unconnected input" in str(context.exception))

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

        with self.assertRaises(FinamStatusError) as context:
            composition.run(t_max=datetime(2000, 1, 31))


if __name__ == "__main__":
    unittest.main()
