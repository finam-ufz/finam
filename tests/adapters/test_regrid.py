"""
Unit tests for data info propagation.
"""
import unittest
from datetime import datetime, timedelta

import numpy as np
import pint

from finam.adapters.regrid import Linear, Nearest
from finam.core.interfaces import ComponentStatus, FinamMetaDataError
from finam.core.schedule import Composition
from finam.core.sdk import ATimeComponent, Input
from finam.data import Info
from finam.data.grid_spec import RectilinearGrid, UniformGrid
from finam.data.grid_tools import Location
from finam.modules.generators import CallbackGenerator


class MockupConsumer(ATimeComponent):
    def __init__(self, time, grid_spec):
        super().__init__()
        self.status = ComponentStatus.CREATED
        self.time = time
        self.step = timedelta(days=1)
        self.grid_spec = grid_spec
        self.data = None

    def _initialize(self):
        self.inputs.add(name="Input")
        self.create_connector(required_in_data=["Input"])

    def _connect(self):
        self.try_connect(self.time, exchange_infos={"Input": Info(grid=self.grid_spec)})
        self.data = self.connector.in_data["Input"]

    def _validate(self):
        pass

    def _update(self):
        self.data = self.inputs["Input"].pull_data(self.time)
        self.time += self.step

    def _finalize(self):
        pass


class TestRegrid(unittest.TestCase):
    def test_regrid_nearest(self):
        reg = pint.UnitRegistry(force_ndarray_like=True)

        in_info = Info(
            grid=UniformGrid(
                dims=(5, 10), spacing=(3.0, 3.0, 3.0), data_location=Location.POINTS
            ),
            units="m",
        )

        out_spec = UniformGrid(dims=(14, 29), data_location=Location.POINTS)

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: in_data,
                    in_info,
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(datetime(2000, 1, 1), out_spec)

        composition = Composition([source, sink])
        composition.initialize()

        (source.outputs["Output"] >> Nearest() >> sink.inputs["Input"])

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data[0, 0, 0], 1.0 * reg.meter)
        self.assertEqual(sink.data[0, 0, 1], 1.0 * reg.meter)
        self.assertEqual(sink.data[0, 1, 0], 1.0 * reg.meter)
        self.assertEqual(sink.data[0, 1, 1], 1.0 * reg.meter)
        self.assertEqual(sink.data[0, 0, 2], 0.0 * reg.meter)
        self.assertEqual(sink.data[0, 2, 0], 0.0 * reg.meter)
        self.assertEqual(sink.data[0, 2, 2], 0.0 * reg.meter)

    def test_regrid_linear(self):
        reg = pint.UnitRegistry(force_ndarray_like=True)

        in_info = Info(
            grid=UniformGrid(
                dims=(5, 10), spacing=(2.0, 2.0, 2.0), data_location=Location.POINTS
            ),
            units="m",
        )
        out_spec = UniformGrid(dims=(9, 19), data_location=Location.POINTS)

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(datetime(2000, 1, 1), out_spec)

        composition = Composition([source, sink])
        composition.initialize()

        (source.outputs["Output"] >> Linear() >> sink.inputs["Input"])

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data[0, 0, 0], 1.0 * reg.meter)
        self.assertEqual(sink.data[0, 0, 1], 0.5 * reg.meter)
        self.assertEqual(sink.data[0, 1, 0], 0.5 * reg.meter)
        self.assertEqual(sink.data[0, 1, 1], 0.25 * reg.meter)

    def test_regrid_linear_custom(self):
        reg = pint.UnitRegistry(force_ndarray_like=True)

        in_info = Info(
            grid=UniformGrid(
                dims=(5, 10), spacing=(2.0, 2.0, 2.0), data_location=Location.POINTS
            ),
            units="m",
        )
        out_spec = UniformGrid(dims=(9, 19), data_location=Location.POINTS)

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, Info(grid=None, units="m"))},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(datetime(2000, 1, 1), None)

        composition = Composition([source, sink])
        composition.initialize()

        (
            source.outputs["Output"]
            >> Linear(in_grid=in_info.grid, out_grid=out_spec)
            >> sink.inputs["Input"]
        )

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data[0, 0, 0], 1.0 * reg.meter)
        self.assertEqual(sink.data[0, 0, 1], 0.5 * reg.meter)
        self.assertEqual(sink.data[0, 1, 0], 0.5 * reg.meter)
        self.assertEqual(sink.data[0, 1, 1], 0.25 * reg.meter)

    def test_regrid_linear_rev(self):
        reg = pint.UnitRegistry(force_ndarray_like=True)

        in_info = Info(
            RectilinearGrid(
                axes=[np.linspace(8, 0, 5), np.linspace(0, 18, 10)],
                data_location=Location.POINTS,
            ),
            units="m",
        )
        out_spec = UniformGrid(dims=(9, 19), data_location=Location.POINTS)

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(datetime(2000, 1, 1), out_spec)

        composition = Composition([source, sink])
        composition.initialize()

        (source.outputs["Output"] >> Linear() >> sink.inputs["Input"])

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data[0, 0, 0], 1.0 * reg.meter)
        self.assertEqual(sink.data[0, 0, 1], 0.5 * reg.meter)
        self.assertEqual(sink.data[0, 1, 0], 0.5 * reg.meter)
        self.assertEqual(sink.data[0, 1, 1], 0.25 * reg.meter)

    def test_regrid_multi(self):
        reg = pint.UnitRegistry(force_ndarray_like=True)

        in_info = Info(
            UniformGrid(
                dims=(5, 10), spacing=(2.0, 2.0, 2.0), data_location=Location.POINTS
            ),
            units="m",
        )
        out_spec_1 = UniformGrid(dims=(9, 19), data_location=Location.POINTS)
        out_spec_2 = UniformGrid(dims=(9, 19), data_location=Location.POINTS)

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink_1 = MockupConsumer(datetime(2000, 1, 1), out_spec_1)
        sink_2 = MockupConsumer(datetime(2000, 1, 1), out_spec_2)

        regrid = Linear()

        composition = Composition([source, sink_1, sink_2])
        composition.initialize()

        source.outputs["Output"] >> regrid
        regrid >> sink_1.inputs["Input"]
        regrid >> sink_2.inputs["Input"]

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink_1.inputs["Input"].info.grid, out_spec_1)
        self.assertEqual(sink_1.data[0, 0, 0], 1.0 * reg.meter)
        self.assertEqual(sink_1.data[0, 0, 1], 0.5 * reg.meter)
        self.assertEqual(sink_1.data[0, 1, 0], 0.5 * reg.meter)
        self.assertEqual(sink_1.data[0, 1, 1], 0.25 * reg.meter)

        self.assertEqual(sink_2.inputs["Input"].info.grid, out_spec_2)
        self.assertEqual(sink_2.data[0, 0, 0], 1.0 * reg.meter)
        self.assertEqual(sink_2.data[0, 0, 1], 0.5 * reg.meter)
        self.assertEqual(sink_2.data[0, 1, 0], 0.5 * reg.meter)
        self.assertEqual(sink_2.data[0, 1, 1], 0.25 * reg.meter)

    def test_regrid_multi_fail(self):
        reg = pint.UnitRegistry(force_ndarray_like=True)

        in_info = Info(
            UniformGrid(
                dims=(5, 10), spacing=(2.0, 2.0, 2.0), data_location=Location.POINTS
            ),
            units="m",
        )
        out_spec_1 = UniformGrid(dims=(9, 19), data_location=Location.POINTS)
        out_spec_2 = UniformGrid(dims=(8, 18), data_location=Location.POINTS)

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink_1 = MockupConsumer(datetime(2000, 1, 1), out_spec_1)
        sink_2 = MockupConsumer(datetime(2000, 1, 1), out_spec_2)

        regrid = Linear()

        composition = Composition([source, sink_1, sink_2])
        composition.initialize()

        source.outputs["Output"] >> regrid
        regrid >> sink_1.inputs["Input"]
        regrid >> sink_2.inputs["Input"]

        with self.assertRaises(FinamMetaDataError) as _context:
            composition.run(t_max=datetime(2000, 1, 2))
