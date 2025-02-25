"""
Unit tests for data info propagation.
"""

import unittest
from datetime import datetime, timedelta

import numpy as np

from finam import (
    UNITS,
    CellType,
    Composition,
    FinamDataError,
    FinamMetaDataError,
    Info,
    Location,
    RectilinearGrid,
    UniformGrid,
    UnstructuredGrid,
)
from finam import data as fdata
from finam.adapters.regrid import RegridLinear, RegridNearest
from finam.components import debug, generators


class TestRegrid(unittest.TestCase):
    def test_regrid_nearest(self):
        time = datetime(2000, 1, 1)

        in_info = Info(
            time=time,
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
            {"Input": Info(None, grid=out_spec, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink], log_level="DEBUG")

        (source.outputs["Output"] >> RegridNearest() >> sink.inputs["Input"])

        composition.connect()

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data["Input"][0, 0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 1], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 1], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 2], 0.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 2, 0], 0.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 2, 2], 0.0 * UNITS.meter)

    def test_regrid_nearest_masked(self):
        time = datetime(2000, 1, 1)

        in_info = Info(
            time=time,
            grid=UniformGrid(
                dims=(5, 10), spacing=(3.0, 3.0, 3.0), data_location=Location.POINTS
            ),
            units="m",
        )

        out_spec = UniformGrid(dims=(14, 29), data_location=Location.POINTS)

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        in_data = np.ma.masked_where(in_data > 0, in_data)

        source = generators.CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: in_data.copy(),
                    in_info,
                )
            },
            start=time,
            step=timedelta(days=1),
        )

        sink = debug.DebugConsumer(
            {"Input": Info(None, grid=out_spec, units=None)},
            start=time,
            step=timedelta(days=1),
        )

        composition = Composition([source, sink], log_level="DEBUG")

        (source.outputs["Output"] >> RegridNearest() >> sink.inputs["Input"])

        with self.assertRaises(FinamDataError):
            composition.connect()

    def test_regrid_nearest_crs(self):
        time = datetime(2000, 1, 1)
        in_info = Info(
            time=time,
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
            {"Input": Info(None, grid=out_spec, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink])

        (source.outputs["Output"] >> RegridNearest() >> sink.inputs["Input"])

        composition.connect()

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data["Input"][0, 0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 1], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 1], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 2], 0.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 2, 0], 0.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 2, 2], 0.0 * UNITS.meter)

    def test_regrid_linear(self):
        time = datetime(2000, 1, 1)
        in_info = Info(
            time=time,
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
            {"Input": Info(None, grid=out_spec, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink])

        (source.outputs["Output"] >> RegridLinear() >> sink.inputs["Input"])

        composition.connect()

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data["Input"][0, 0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 1], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 0], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 1], 0.25 * UNITS.meter)

    def test_regrid_linear_masked(self):
        time = datetime(2000, 1, 1)

        in_info = Info(
            time=time,
            grid=UniformGrid(
                dims=(5, 10), spacing=(3.0, 3.0, 3.0), data_location=Location.POINTS
            ),
            units="m",
        )

        out_spec = UniformGrid(dims=(14, 29), data_location=Location.POINTS)

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        in_data = np.ma.masked_where(in_data > 0, in_data)

        source = generators.CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: in_data.copy(),
                    in_info,
                )
            },
            start=time,
            step=timedelta(days=1),
        )

        sink = debug.DebugConsumer(
            {"Input": Info(None, grid=out_spec, units=None)},
            start=time,
            step=timedelta(days=1),
        )

        composition = Composition([source, sink], log_level="DEBUG")

        (
            source.outputs["Output"]
            >> RegridLinear(fill_with_nearest=True)
            >> sink.inputs["Input"]
        )

        with self.assertRaises(FinamDataError):
            composition.connect()

    def test_regrid_linear_crs(self):
        time = datetime(2000, 1, 1)
        in_info = Info(
            time=time,
            grid=UniformGrid(
                dims=(5, 10),
                spacing=(2.0, 2.0, 2.0),
                data_location=Location.POINTS,
                crs="EPSG:32632",
            ),
            units="m",
        )
        out_spec = UniformGrid(
            dims=(9, 19), data_location=Location.POINTS, crs="EPSG:25832"
        )

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = generators.CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = debug.DebugConsumer(
            {"Input": Info(None, grid=out_spec, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink])

        (
            source.outputs["Output"]
            >> RegridLinear(fill_with_nearest=True)
            >> sink.inputs["Input"]
        )

        composition.connect()

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertAlmostEqual(fdata.get_magnitude(sink.data["Input"])[0, 0, 0], 1.0)
        self.assertAlmostEqual(fdata.get_magnitude(sink.data["Input"])[0, 0, 1], 0.5)
        self.assertAlmostEqual(fdata.get_magnitude(sink.data["Input"])[0, 1, 0], 0.5)
        self.assertAlmostEqual(fdata.get_magnitude(sink.data["Input"])[0, 1, 1], 0.25)

    def test_regrid_linear_custom(self):
        time = datetime(2000, 1, 1)
        in_info = Info(
            time=time,
            grid=UniformGrid(
                dims=(5, 10), spacing=(2.0, 2.0, 2.0), data_location=Location.POINTS
            ),
            units="m",
        )
        out_spec = UniformGrid(dims=(9, 19), data_location=Location.POINTS)

        in_data = np.zeros(shape=in_info.grid.data_shape, order=in_info.grid.order)
        in_data.data[0, 0] = 1.0

        source = generators.CallbackGenerator(
            callbacks={
                "Output": (lambda t: in_data, Info(time=None, grid=None, units="m"))
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = debug.DebugConsumer(
            {"Input": Info(None, grid=None, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink])

        (
            source.outputs["Output"]
            >> RegridLinear(in_grid=in_info.grid, out_grid=out_spec)
            >> sink.inputs["Input"]
        )

        composition.connect()

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data["Input"][0, 0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 1], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 0], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 1], 0.25 * UNITS.meter)

    def test_regrid_linear_rev(self):
        time = datetime(2000, 1, 1)
        in_info = Info(
            time=time,
            grid=RectilinearGrid(
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
            {"Input": Info(None, grid=out_spec, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink])

        (source.outputs["Output"] >> RegridLinear() >> sink.inputs["Input"])

        composition.connect()

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data["Input"][0, 0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 0, 1], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 0], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1, 1], 0.25 * UNITS.meter)

    def test_regrid_multi(self):
        time = datetime(2000, 1, 1)
        in_info = Info(
            time=time,
            grid=UniformGrid(
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
            {"Input": Info(None, grid=out_spec_1, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        sink_2 = debug.DebugConsumer(
            {"Input": Info(None, grid=out_spec_2, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        regrid = RegridLinear()

        composition = Composition([source, sink_1, sink_2])

        source.outputs["Output"] >> regrid
        regrid >> sink_1.inputs["Input"]
        regrid >> sink_2.inputs["Input"]

        composition.connect()

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
        time = datetime(2000, 1, 1)
        in_info = Info(
            time=time,
            grid=UniformGrid(
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
            {"Input": Info(None, grid=out_spec_1, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        sink_2 = debug.DebugConsumer(
            {"Input": Info(None, grid=out_spec_2, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        regrid = RegridLinear()

        composition = Composition([source, sink_1, sink_2])

        source.outputs["Output"] >> regrid
        regrid >> sink_1.inputs["Input"]
        regrid >> sink_2.inputs["Input"]

        with self.assertRaises(FinamMetaDataError) as _context:
            composition.run(end_time=datetime(2000, 1, 2))

    def test_regrid_linear_unstructured(self):
        time = datetime(2000, 1, 1)
        g1 = UniformGrid(
            dims=(5, 10),
            spacing=(2.0, 2.0, 2.0),
            data_location=Location.POINTS,
        )
        g2 = UniformGrid(dims=(9, 19), data_location=Location.POINTS)

        in_info = Info(
            time=time,
            grid=UnstructuredGrid(
                points=g1.data_points,
                cells=g1.cells,
                cell_types=[CellType.QUAD] * g1.data_size,
                data_location="POINTS",
            ),
            units="m",
        )
        out_spec = UnstructuredGrid(
            points=g2.data_points,
            cells=g2.cells,
            cell_types=[CellType.QUAD] * g2.data_size,
            data_location="POINTS",
        )

        in_data = np.zeros(shape=in_info.grid.data_size)
        in_data.data[0] = 1.0

        source = generators.CallbackGenerator(
            callbacks={"Output": (lambda t: in_data, in_info)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        sink = debug.DebugConsumer(
            {"Input": Info(None, grid=out_spec, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = Composition([source, sink])

        (
            source.outputs["Output"]
            >> RegridLinear(fill_with_nearest=True)
            >> sink.inputs["Input"]
        )

        composition.connect()

        self.assertEqual(sink.inputs["Input"].info.grid, out_spec)
        self.assertEqual(sink.data["Input"][0, 0], 1.0 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 1], 0.5 * UNITS.meter)
        self.assertEqual(sink.data["Input"][0, 9], 0.5 * UNITS.meter)


if __name__ == "__main__":
    unittest.main()
