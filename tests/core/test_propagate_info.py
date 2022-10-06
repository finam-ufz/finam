"""
Unit tests for data info propagation.
"""
import copy
import unittest
from datetime import datetime, timedelta

from finam.core.interfaces import ComponentStatus, FinamNoDataError
from finam.core.schedule import Composition
from finam.core.sdk import AAdapter, ATimeComponent, Input, Output
from finam.data import Info
from finam.modules.generators import CallbackGenerator


class MockupConsumer(ATimeComponent):
    def __init__(self, time, info):
        super().__init__()
        self.status = ComponentStatus.CREATED
        self.time = time
        self.step = timedelta(days=1)
        self.info = info
        self.data = None

    def initialize(self):
        super().initialize()
        self._inputs["Input"] = Input()
        self.status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        try:
            self.inputs["Input"].exchange_info(self.info)
        except FinamNoDataError:
            self.status = ComponentStatus.CONNECTING_IDLE
            return

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


class MockupProducer(ATimeComponent):
    def __init__(self, time, info):
        super().__init__()
        self.status = ComponentStatus.CREATED
        self.time = time
        self.step = timedelta(days=1)
        self.info = info

    def initialize(self):
        super().initialize()
        self.outputs["Output"] = Output(self.info)
        self.status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()
        try:
            _info = self.outputs["Output"].info
        except FinamNoDataError:
            self.status = ComponentStatus.CONNECTING_IDLE
            return

        self.status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()
        self.status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        self.time += self.step
        self.outputs["Output"].push_data(1, self.time)

        self.status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()
        self.status = ComponentStatus.FINALIZED


class SpecAdapter(AAdapter):
    def __init__(self):
        super().__init__()

    def get_data(self, time):
        return self.pull_data(time)

    def get_info(self, info):
        self.logger.debug("get info")

        in_info = self.exchange_info(info)
        out_info = in_info.copy_with(grid=info.grid)
        return out_info


class UnitAdapter(AAdapter):
    def __init__(self):
        super().__init__()

    def get_data(self, time):
        return self.pull_data(time)

    def get_info(self, info):
        self.logger.debug("get info")

        in_info = self.exchange_info(info)
        out_info = copy.copy(in_info)
        if "unit" in info.meta:
            out_info.meta["unit"] = info.meta["unit"]
        return out_info


class TestPropagate(unittest.TestCase):
    def test_propagate_info(self):
        source = CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: 1,
                    Info(grid="source_spec", meta={"unit": "source_unit"}),
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(
            datetime(2000, 1, 1), Info(grid="sink_spec", meta={"unit": "sink_unit"})
        )

        composition = Composition([source, sink])
        composition.initialize()

        (
            source.outputs["Output"]
            >> SpecAdapter()
            >> UnitAdapter()
            >> sink.inputs["Input"]
        )

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(
            sink.inputs["Input"].info,
            Info(grid="sink_spec", meta={"unit": "sink_unit"}),
        )

    def test_propagate_info_from_source(self):
        source = CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: 1,
                    Info(grid="source_spec", meta={"unit": "source_unit"}),
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(
            datetime(2000, 1, 1), Info(grid=None, meta={"unit": None})
        )

        composition = Composition([source, sink])
        composition.initialize()

        source.outputs["Output"] >> sink.inputs["Input"]

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(
            sink.inputs["Input"].info,
            Info(grid="source_spec", meta={"unit": "source_unit"}),
        )

    def test_propagate_info_from_target(self):
        source = MockupProducer(
            time=datetime(2000, 1, 1), info=Info(grid=None, meta={"unit": None})
        )

        sink = MockupConsumer(
            datetime(2000, 1, 1), Info(grid="sink_spec", meta={"unit": "sink_unit"})
        )

        composition = Composition([source, sink])
        composition.initialize()

        source.outputs["Output"] >> sink.inputs["Input"]

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(
            source.outputs["Output"].info,
            Info(grid="sink_spec", meta={"unit": "sink_unit"}),
        )
