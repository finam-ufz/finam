"""
Unit tests for data info propagation.
"""
import unittest
from datetime import datetime, timedelta

import numpy as np

from finam.adapters.units import ConvertUnits
from finam.core.interfaces import ComponentStatus
from finam.core.schedule import Composition
from finam.core.sdk import ATimeComponent, Input
from finam.data import Info, tools
from finam.data.grid_spec import UniformGrid
from finam.data.grid_tools import Location
from finam.modules.generators import CallbackGenerator
from finam.tools.connect_helper import ConnectHelper


class MockupConsumer(ATimeComponent):
    def __init__(self, time, units):
        super().__init__()
        self.status = ComponentStatus.CREATED
        self.time = time
        self.step = timedelta(days=1)
        self.units = units
        self.data = None
        self._connector = None

    def initialize(self):
        super().initialize()
        self.inputs.add(name="Input", info=Info(units=self.units))
        self._connector = ConnectHelper(
            self.inputs, self.outputs, required_in_data=["Input"]
        )
        self.status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()
        self.status = self._connector.connect(self.time)

        data = self._connector.in_data["Input"]
        if data is not None:
            self.data = data

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


class TestUnits(unittest.TestCase):
    def test_units(self):
        in_info = Info(
            grid=UniformGrid(
                dims=(5, 10), spacing=(2.0, 2.0, 2.0), data_location=Location.POINTS
            ),
            units=tools.UNITS.meter,
        )

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(datetime(2000, 1, 1), tools.UNITS.kilometer)

        composition = Composition([source, sink])
        composition.initialize()

        (source.outputs["Output"] >> ConvertUnits() >> sink.inputs["Input"])

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(
            sink.inputs["Input"].info.meta, {"units": tools.UNITS.kilometer}
        )
        self.assertEqual(tools.get_units(sink.data), tools.UNITS.kilometer)
        self.assertEqual(tools.get_magnitude(sink.data)[0, 0, 0], 0.001)
