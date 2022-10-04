"""
Unit tests for data info propagation.
"""
import unittest
from datetime import datetime, timedelta

import numpy as np
import pint
import pint_xarray
import xarray as xr

from finam.adapters.regrid import Regrid
from finam.core.interfaces import ComponentStatus, FinamMetaDataError
from finam.core.schedule import Composition
from finam.core.sdk import AAdapter, ATimeComponent, Input
from finam.data.grid_spec import UniformGrid
from finam.data.grid_tools import Location
from finam.modules.generators import CallbackGenerator


class MockupConsumer(ATimeComponent):
    def __init__(self, time, grid_spec):
        super().__init__()
        self.status = ComponentStatus.CREATED
        self.time = time
        self.step = timedelta(days=1)
        self.grid_spec = grid_spec
        self.info = None
        self.data = None

    def initialize(self):
        super().initialize()
        self._inputs["Input"] = Input()
        self.status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()
        self.info = self.inputs["Input"].pull_info({"grid_spec": self.grid_spec})
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


class TestRegrid(unittest.TestCase):
    def test_regrid(self):
        reg = pint.UnitRegistry(force_ndarray_like=True)

        in_spec = UniformGrid(
            dims=(5, 10), spacing=(2.0, 2.0, 2.0), data_location=Location.POINTS
        )
        out_spec = UniformGrid(dims=(9, 19), data_location=Location.POINTS)

        in_data = xr.DataArray(
            np.zeros(shape=in_spec.data_shape, order=in_spec.order)
        ).pint.quantify(reg.meter)
        in_data.data[0, 0] = 1.0 * in_data.pint.units

        source = CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, {"grid_spec": in_spec})},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = MockupConsumer(datetime(2000, 1, 1), out_spec)

        composition = Composition([source, sink])
        composition.initialize()

        (source.outputs["Output"] >> Regrid() >> sink.inputs["Input"])

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.info, {"grid_spec": out_spec})
        self.assertEqual(sink.data[0, 0], 1.0 * reg.meter)
        self.assertEqual(sink.data[0, 1], 0.5 * reg.meter)
        self.assertEqual(sink.data[1, 0], 0.5 * reg.meter)
        self.assertEqual(sink.data[1, 1], 0.25 * reg.meter)

    def test_regrid_multi(self):
        reg = pint.UnitRegistry(force_ndarray_like=True)

        in_spec = UniformGrid(
            dims=(5, 10), spacing=(2.0, 2.0, 2.0), data_location=Location.POINTS
        )
        out_spec_1 = UniformGrid(dims=(9, 19), data_location=Location.POINTS)
        out_spec_2 = UniformGrid(dims=(9, 19), data_location=Location.POINTS)

        in_data = xr.DataArray(
            np.zeros(shape=in_spec.data_shape, order=in_spec.order)
        ).pint.quantify(reg.meter)
        in_data.data[0, 0] = 1.0 * in_data.pint.units

        source = CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, {"grid_spec": in_spec})},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink_1 = MockupConsumer(datetime(2000, 1, 1), out_spec_1)
        sink_2 = MockupConsumer(datetime(2000, 1, 1), out_spec_2)

        regrid = Regrid()

        composition = Composition([source, sink_1, sink_2])
        composition.initialize()

        source.outputs["Output"] >> regrid
        regrid >> sink_1.inputs["Input"]
        regrid >> sink_2.inputs["Input"]

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink_1.info, {"grid_spec": out_spec_1})
        self.assertEqual(sink_1.data[0, 0], 1.0 * reg.meter)
        self.assertEqual(sink_1.data[0, 1], 0.5 * reg.meter)
        self.assertEqual(sink_1.data[1, 0], 0.5 * reg.meter)
        self.assertEqual(sink_1.data[1, 1], 0.25 * reg.meter)

        self.assertEqual(sink_2.info, {"grid_spec": out_spec_2})
        self.assertEqual(sink_2.data[0, 0], 1.0 * reg.meter)
        self.assertEqual(sink_2.data[0, 1], 0.5 * reg.meter)
        self.assertEqual(sink_2.data[1, 0], 0.5 * reg.meter)
        self.assertEqual(sink_2.data[1, 1], 0.25 * reg.meter)

    def test_regrid_multi_fail(self):
        reg = pint.UnitRegistry(force_ndarray_like=True)

        in_spec = UniformGrid(
            dims=(5, 10), spacing=(2.0, 2.0, 2.0), data_location=Location.POINTS
        )
        out_spec_1 = UniformGrid(dims=(9, 19), data_location=Location.POINTS)
        out_spec_2 = UniformGrid(dims=(8, 18), data_location=Location.POINTS)

        in_data = xr.DataArray(
            np.zeros(shape=in_spec.data_shape, order=in_spec.order)
        ).pint.quantify(reg.meter)
        in_data.data[0, 0] = 1.0 * in_data.pint.units

        source = CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, {"grid_spec": in_spec})},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink_1 = MockupConsumer(datetime(2000, 1, 1), out_spec_1)
        sink_2 = MockupConsumer(datetime(2000, 1, 1), out_spec_2)

        regrid = Regrid()

        composition = Composition([source, sink_1, sink_2])
        composition.initialize()

        source.outputs["Output"] >> regrid
        regrid >> sink_1.inputs["Input"]
        regrid >> sink_2.inputs["Input"]

        with self.assertRaises(FinamMetaDataError) as _context:
            composition.run(t_max=datetime(2000, 1, 2))
