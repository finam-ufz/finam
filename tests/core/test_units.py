"""
Unit tests for data info propagation.
"""
import unittest
from datetime import datetime, timedelta

import numpy as np

from finam import (
    UNITS,
    ATimeComponent,
    ComponentStatus,
    Composition,
    FinamMetaDataError,
    Info,
    Location,
    UniformGrid,
)
from finam import data as tools
from finam.modules.generators import CallbackGenerator


class MockupConsumer(ATimeComponent):
    def __init__(self, time, units):
        super().__init__()
        self.status = ComponentStatus.CREATED
        self.time = time
        self.step = timedelta(days=1)
        self.units = units
        self.data = None

    def _initialize(self):
        self.inputs.add(name="Input", grid=None, units=self.units)
        self.create_connector(required_in_data=["Input"])

    def _connect(self):
        self.try_connect(self.time)

        data = self.connector.in_data["Input"]
        if data is not None:
            self.data = data

    def _validate(self):
        pass

    def _update(self):
        self.data = self.inputs["Input"].pull_data(self.time)
        self.time += self.step

    def _finalize(self):
        pass


class TestUnits(unittest.TestCase):
    def test_units(self):
        in_info = Info(
            grid=UniformGrid(
                dims=(5, 10), spacing=(2.0, 2.0, 2.0), data_location=Location.POINTS
            ),
            units=UNITS.meter,
        )

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(datetime(2000, 1, 1), UNITS.kilometer)

        composition = Composition([source, sink])
        composition.initialize()

        (source.outputs["Output"] >> sink.inputs["Input"])

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.inputs["Input"].info.meta, {"units": UNITS.kilometer})
        self.assertEqual(tools.get_units(sink.data), UNITS.kilometer)
        self.assertEqual(tools.get_magnitude(sink.data)[0, 0, 0], 0.001)

    def test_units_fail(self):
        in_info = Info(
            grid=UniformGrid(
                dims=(5, 10), spacing=(2.0, 2.0, 2.0), data_location=Location.POINTS
            ),
            units=UNITS.meter,
        )

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(datetime(2000, 1, 1), UNITS.seconds)

        composition = Composition([source, sink])
        composition.initialize()

        (source.outputs["Output"] >> sink.inputs["Input"])

        with self.assertRaises(FinamMetaDataError):
            composition.run(t_max=datetime(2000, 1, 2))