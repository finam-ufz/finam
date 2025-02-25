"""
Unit tests for data info propagation.
"""

import unittest
from datetime import datetime, timedelta

import numpy as np

from finam import (
    UNITS,
    Composition,
    FinamMetaDataError,
    Info,
    Location,
    TimeComponent,
    UniformGrid,
)
from finam import data as tools
from finam.components.generators import CallbackGenerator


class MockupConsumer(TimeComponent):
    def __init__(self, time, units):
        super().__init__()
        self.time = time
        self.step = timedelta(days=1)
        self.units = units
        self.data = None

    def _next_time(self):
        return self.time + self.step

    def _initialize(self):
        self.inputs.add(name="Input", time=self.time, grid=None, units=self.units)
        self.create_connector(pull_data=["Input"])

    def _connect(self, start_time):
        self.try_connect(start_time)

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
        time = datetime(2000, 1, 1)

        in_info = Info(
            time=time,
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

        (source.outputs["Output"] >> sink.inputs["Input"])

        composition.connect()

        self.assertEqual(sink.inputs["Input"].info.meta, {"units": UNITS.kilometer})
        self.assertEqual(tools.get_units(sink.data), UNITS.kilometer)
        self.assertEqual(tools.get_magnitude(sink.data)[0, 0, 0], 0.001)

    def test_units_fail(self):
        time = datetime(2000, 1, 1)

        in_info = Info(
            time=time,
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

        (source.outputs["Output"] >> sink.inputs["Input"])

        with self.assertRaises(FinamMetaDataError):
            composition.run(start_time=time, end_time=datetime(2000, 1, 2))


if __name__ == "__main__":
    unittest.main()
