"""
Unit tests for data info propagation.
"""

import unittest
from datetime import datetime, timedelta

from finam.core.interfaces import ComponentStatus, FinamStatusError
from finam.core.schedule import Composition
from finam.core.sdk import AAdapter, ATimeComponent, Input, Output
from finam.modules.generators import CallbackGenerator


class MockupConsumer(ATimeComponent):
    def __init__(self, time):
        super().__init__()
        self.status = ComponentStatus.CREATED
        self.time = time
        self.step = timedelta(days=1)
        self.info = None
        self.data = None

    def initialize(self):
        super().initialize()
        self._inputs["Input"] = Input()
        self.status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()
        self.info = self.inputs["Input"].pull_info(
            {"spec": "sink_spec", "unit": "sink_unit"}
        )
        self.data = self.inputs["Input"].pull_data(self.time)
        self.status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()
        self.status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        self.data = self.inputs["Input"].pull_data(self.time)
        self.time += self.step

        self.status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()
        self.status = ComponentStatus.FINALIZED


class SpecAdapter(AAdapter):
    def __init__(self):
        super().__init__()

    def get_data(self, time):
        return self.pull_data(time)

    def get_info(self, request_params):
        self.logger.debug("get info")

        info = self.pull_info(request_params)
        out_info = dict(info)
        if "spec" in request_params:
            out_info["spec"] = request_params["spec"]
            print(f"convert from spec '{info['spec']}' to '{request_params['spec']}'")
        return out_info


class UnitAdapter(AAdapter):
    def __init__(self):
        super().__init__()

    def get_data(self, time):
        return self.pull_data(time)

    def get_info(self, request_params):
        self.logger.debug("get info")

        info = self.pull_info(request_params)
        out_info = dict(info)
        if "unit" in request_params:
            out_info["unit"] = request_params["unit"]
            print(f"convert from unit '{info['unit']}' to '{request_params['unit']}'")
        return out_info


class TestPropagate(unittest.TestCase):
    def test_propagate_info(self):
        source = CallbackGenerator(
            callbacks={
                "Output": (lambda t: 1, {"spec": "source_spec", "unit": "source_unit"})
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(datetime(2000, 1, 1))

        composition = Composition([source, sink])
        composition.initialize()

        (
            source.outputs["Output"]
            >> SpecAdapter()
            >> UnitAdapter()
            >> sink.inputs["Input"]
        )

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.info, {"spec": "sink_spec", "unit": "sink_unit"})
