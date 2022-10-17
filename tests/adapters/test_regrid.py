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
    RectilinearGrid,
    UniformGrid,
)
from finam import data as fdata
from finam.adapters.regrid import Linear, Nearest
from finam.modules import debug, generators


class TestRegrid(unittest.TestCase):
    def test_regrid_nearest(self):
        in_info = Info(
            grid=UniformGrid(
                dims=(5, 10), spacing=(3.0, 3.0, 3.0), data_location=Location.POINTS
            ),
            units="m",
        )

        out_spec = UniformGrid(dims=(14, 29), data_location=Location.POINTS)

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = generators.CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: in_data,
                    in_info,
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = debug.DebugConsumer(
            {"Input": Info(grid=out_spec)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink])
        composition.initialize()

        (source.outputs["Output"] >> Nearest() >> sink.inputs["Input"])

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data["Input"][0, 0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 1], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 1], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 2], 0.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 2, 0], 0.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 2, 2], 0.0 * UNITS.meter)

    def test_regrid_nearest_crs(self):
        in_info = Info(
            grid=UniformGrid(
                dims=(5, 10),
                spacing=(3.0, 3.0, 3.0),
                data_location=Location.POINTS,
                crs="EPSG:32632",
            ),
            units="m",
        )

        out_spec = UniformGrid(
            dims=(14, 29), data_location=Location.POINTS, crs="EPSG:25832"
        )

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = generators.CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: in_data,
                    in_info,
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = debug.DebugConsumer(
            {"Input": Info(grid=out_spec)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink])
        composition.initialize()

        (source.outputs["Output"] >> Nearest() >> sink.inputs["Input"])

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data["Input"][0, 0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 1], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 1], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 2], 0.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 2, 0], 0.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 2, 2], 0.0 * UNITS.meter)

    def test_regrid_linear(self):
        in_info = Info(
            grid=UniformGrid(
                dims=(5, 10),
                spacing=(2.0, 2.0, 2.0),
                data_location=Location.POINTS,
            ),
            units="m",
        )
        out_spec = UniformGrid(dims=(9, 19), data_location=Location.POINTS)

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = generators.CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = debug.DebugConsumer(
            {"Input": Info(grid=out_spec)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink])
        composition.initialize()

        (source.outputs["Output"] >> Linear() >> sink.inputs["Input"])

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data["Input"][0, 0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 1], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 0], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 1], 0.25 * UNITS.meter)

    def test_regrid_linear_crs(self):
        in_info = Info(
            grid=UniformGrid(
                dims=(5, 10),
                spacing=(2.0, 2.0, 2.0),
                data_location=Location.POINTS,
                crs="EPSG:25832",
            ),
            units="m",
        )
        out_spec = UniformGrid(
            dims=(9, 19), data_location=Location.POINTS, crs="EPSG:32632"
        )

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = generators.CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = debug.DebugConsumer(
            {"Input": Info(grid=out_spec)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink])
        composition.initialize()

        (
            source.outputs["Output"]
            >> Linear(fill_with_nearest=True)
            >> sink.inputs["Input"]
        )

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertAlmostEqual(fdata.get_magnitude(sink.data["Input"])[0, 0, 0], 1.0)
        self.assertAlmostEqual(fdata.get_magnitude(sink.data["Input"])[0, 0, 1], 0.5)
        self.assertAlmostEqual(fdata.get_magnitude(sink.data["Input"])[0, 1, 0], 0.5)
        self.assertAlmostEqual(fdata.get_magnitude(sink.data["Input"])[0, 1, 1], 0.25)

    def test_regrid_linear_custom(self):
        in_info = Info(
            grid=UniformGrid(
                dims=(5, 10), spacing=(2.0, 2.0, 2.0), data_location=Location.POINTS
            ),
            units="m",
        )
        out_spec = UniformGrid(dims=(9, 19), data_location=Location.POINTS)

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = generators.CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, Info(grid=None, units="m"))},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = debug.DebugConsumer(
            {"Input": Info(grid=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink])
        composition.initialize()

        (
            source.outputs["Output"]
            >> Linear(in_grid=in_info.grid, out_grid=out_spec)
            >> sink.inputs["Input"]
        )

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data["Input"][0, 0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 1], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 0], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 1], 0.25 * UNITS.meter)

    def test_regrid_linear_rev(self):
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

        source = generators.CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = debug.DebugConsumer(
            {"Input": Info(grid=out_spec)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink])
        composition.initialize()

        (source.outputs["Output"] >> Linear() >> sink.inputs["Input"])

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data["Input"][0, 0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 1], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 0], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 1], 0.25 * UNITS.meter)

    def test_regrid_multi(self):
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

        source = generators.CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink_1 = debug.DebugConsumer(
            {"Input": Info(grid=out_spec_1)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        sink_2 = debug.DebugConsumer(
            {"Input": Info(grid=out_spec_2)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        regrid = Linear()

        composition = Composition([source, sink_1, sink_2])
        composition.initialize()

        source.outputs["Output"] >> regrid
        regrid >> sink_1.inputs["Input"]
        regrid >> sink_2.inputs["Input"]

        composition.run(t_max=datetime(2000, 1, 2))

        self.assertEqual(sink_1.inputs["Input"].info.grid, out_spec_1)
        self.assertEqual(sink_1.data["Input"][0, 0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink_1.data["Input"][0, 0, 1], 0.5 * UNITS.meter)
        self.assertEqual(sink_1.data["Input"][0, 1, 0], 0.5 * UNITS.meter)
        self.assertEqual(sink_1.data["Input"][0, 1, 1], 0.25 * UNITS.meter)

        self.assertEqual(sink_2.inputs["Input"].info.grid, out_spec_2)
        self.assertEqual(sink_2.data["Input"][0, 0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink_2.data["Input"][0, 0, 1], 0.5 * UNITS.meter)
        self.assertEqual(sink_2.data["Input"][0, 1, 0], 0.5 * UNITS.meter)
        self.assertEqual(sink_2.data["Input"][0, 1, 1], 0.25 * UNITS.meter)

    def test_regrid_multi_fail(self):
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

        source = generators.CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink_1 = debug.DebugConsumer(
            {"Input": Info(grid=out_spec_1)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        sink_2 = debug.DebugConsumer(
            {"Input": Info(grid=out_spec_2)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        regrid = Linear()

        composition = Composition([source, sink_1, sink_2])
        composition.initialize()

        source.outputs["Output"] >> regrid
        regrid >> sink_1.inputs["Input"]
        regrid >> sink_2.inputs["Input"]

        with self.assertRaises(FinamMetaDataError) as _context:
            composition.run(t_max=datetime(2000, 1, 2))
