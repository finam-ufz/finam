"""
Unit tests for the driver/scheduler.
"""

import unittest
from datetime import datetime, timedelta

from finam.core.interfaces import ComponentStatus, NoBranchAdapter
from finam.core.sdk import ATimeComponent, AAdapter, Input, Output
from finam.core.schedule import Composition


class MockupComponent(ATimeComponent):
    def __init__(self, callbacks, step):
        """
        Create a new CallbackGenerator.
        """
        super(MockupComponent, self).__init__()

        if not isinstance(step, timedelta):
            raise ValueError("Step must be of type timedelta")

        self._callbacks = callbacks
        self._step = step
        self._time = datetime(2000, 1, 1)
        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        for key, _ in self._callbacks.items():
            self._outputs[key] = Output()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        for key, callback in self._callbacks.items():
            self._outputs[key].push_data(callback(self._time), self.time())

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        self._time += self._step

        for key, callback in self._callbacks.items():
            self._outputs[key].push_data(callback(self._time), self.time())

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED


class MockupConsumerComponent(ATimeComponent):
    def __init__(self):
        super(MockupConsumerComponent, self).__init__()
        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()
        self._inputs["Input"] = Input()
        self._status = ComponentStatus.INITIALIZED


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

        self.assertEqual(module.status(), ComponentStatus.INITIALIZED)
        self.assertEqual(len(module.outputs()), 1)

        composition.run(t_max=datetime(2000, 1, 31))

        self.assertEqual(module.status(), ComponentStatus.FINALIZED)
        self.assertEqual(module.time(), datetime(2000, 1, 31))

    def test_check_composition(self):
        with self.assertRaises(AssertionError):
            _comp = Composition(["not a component"])

    def test_validate_branching(self):
        module = MockupComponent(callbacks={"Output": lambda t: t}, step=timedelta(1.0))
        composition = Composition([module])
        composition.initialize()

        non_branching_adapter = (
            module.outputs()["Output"]
            >> NbAdapter()
            >> CallbackAdapter(callback=lambda data, time: data)
        )

        non_branching_adapter >> CallbackAdapter(callback=lambda data, time: data)
        non_branching_adapter >> CallbackAdapter(callback=lambda data, time: data)

        with self.assertRaises(AssertionError) as context:
            composition.validate()

        self.assertTrue("Disallowed branching" in str(context.exception))

    def test_validate_inputs(self):
        module = MockupConsumerComponent()
        composition = Composition([module])
        composition.initialize()

        with self.assertRaises(AssertionError) as context:
            composition.validate()

        self.assertTrue("Unconnected input" in str(context.exception))


if __name__ == "__main__":
    unittest.main()
