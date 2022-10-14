"""
Unit tests for data info propagation.
"""
import copy
import unittest
from datetime import datetime, timedelta

from finam.core.interfaces import ComponentStatus, FinamMetaDataError
from finam.core.schedule import Composition
from finam.core.sdk import AAdapter, ATimeComponent, Input, Output
from finam.data import Info, NoGrid
from finam.modules.generators import CallbackGenerator
from finam.tools.connect_helper import ConnectHelper


class MockupConsumer(ATimeComponent):
    def __init__(self, time, info):
        super().__init__()
        self.status = ComponentStatus.CREATED
        self.time = time
        self.step = timedelta(days=1)
        self.info = info
        self.data = None

        self.connector = None

    def initialize(self):
        super().initialize()
        self.inputs.add(name="Input", info=self.info)
        self.connector = ConnectHelper(self.inputs, self.outputs)
        self.status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()
        self.status = self.connector.connect(self.time)

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

        self.out_info = None

        self.connector = None

    def initialize(self):
        super().initialize()
        self.outputs.add(name="Output", info=self.info)
        self.connector = ConnectHelper(
            self.inputs, self.outputs, required_out_infos=["Output"]
        )
        self.status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()
        self.status = self.connector.connect(self.time, push_data={"Output": 1})
        self.out_info = self.connector.out_infos["Output"]

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
        if "units" in info.meta:
            out_info.meta["units"] = info.meta["units"]
        return out_info


class TestPropagate(unittest.TestCase):
    def test_propagate_info(self):
        source = CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: 1,
                    Info(grid=NoGrid(), meta={"units": "m"}),
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(
            datetime(2000, 1, 1), Info(grid=NoGrid(), meta={"units": "km"})
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
            Info(grid=NoGrid(), meta={"units": "km"}),
        )

    def test_propagate_info_fail(self):
        source = CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: 1,
                    Info(grid=NoGrid(), meta={"units": "m"}),
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(
            datetime(2000, 1, 1), Info(grid=NoGrid(), meta={"units": "m2"})
        )

        composition = Composition([source, sink])
        composition.initialize()

        source.outputs["Output"] >> sink.inputs["Input"]

        with self.assertRaises(FinamMetaDataError):
            composition.run(t_max=datetime(2000, 1, 2))

    def test_propagate_info_from_source(self):
        source = CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: 1,
                    Info(grid=NoGrid(), meta={"units": "m"}),
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(
            datetime(2000, 1, 1), Info(grid=None, meta={"units": None})
        )

        composition = Composition([source, sink])
        composition.initialize()

        source.outputs["Output"] >> sink.inputs["Input"]

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(
            sink.inputs["Input"].info,
            Info(grid=NoGrid(), meta={"units": "m"}),
        )

    def test_propagate_info_from_target(self):
        source = MockupProducer(
            time=datetime(2000, 1, 1), info=Info(grid=None, meta={"units": None})
        )

        sink = MockupConsumer(
            datetime(2000, 1, 1), Info(grid=NoGrid(), meta={"units": "m"})
        )

        composition = Composition([source, sink])
        composition.initialize()

        source.outputs["Output"] >> sink.inputs["Input"]

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(
            source.outputs["Output"].info,
            Info(grid=NoGrid(), meta={"units": "m"}),
        )
        self.assertEqual(
            source.out_info,
            Info(grid=NoGrid(), meta={"units": "m"}),
        )
