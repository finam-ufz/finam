import unittest
from datetime import datetime, timedelta

import numpy as np
from numpy.testing import assert_allclose

import finam as fm


class TestParametricGrid(unittest.TestCase):
    def test_parametric_1d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20,)),
            units="m",
        )

        source = fm.components.ParametricGrid(
            info=in_info,
            func=lambda t, x: x,
        )
        trigger = fm.components.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.components.DebugConsumer(
            {"Input": fm.Info(None, grid=None, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])

        source.outputs["Grid"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"]
        self.assertEqual(data.shape, (1, 19))
        assert_allclose(data[0].magnitude, in_info.grid.data_axes[0])

    def test_parametric_2d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20, 15)),
            units="m",
        )

        source = fm.components.ParametricGrid(
            info=in_info,
            func=lambda t, x, y: x,
        )
        trigger = fm.components.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.components.DebugConsumer(
            {"Input": fm.Info(None, grid=None, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])

        source.outputs["Grid"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"]
        self.assertEqual(data.shape, (1, 19, 14))
        self.assertEqual(data[0, 0, 0], 0.5 * fm.UNITS.Unit("m"))
        self.assertEqual(data[0, 0, 2], 0.5 * fm.UNITS.Unit("m"))
        self.assertEqual(data[0, 2, 2], 2.5 * fm.UNITS.Unit("m"))

    def test_parametric_3d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20, 15, 10)),
            units="m",
        )

        source = fm.components.ParametricGrid(
            info=in_info,
            func=lambda t, x, y, z: x * y - z,
        )
        trigger = fm.components.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.components.DebugConsumer(
            {"Input": fm.Info(None, grid=None, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])

        source.outputs["Grid"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"]
        self.assertEqual(data.shape, (1, 19, 14, 9))

    def test_parametric_points_1d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UnstructuredPoints(np.random.random((100, 1))),
            units="m",
        )

        source = fm.components.ParametricGrid(
            info=in_info,
            func=lambda t, x: x,
        )
        trigger = fm.components.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.components.DebugConsumer(
            {"Input": fm.Info(None, grid=None, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])

        source.outputs["Grid"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"]
        self.assertEqual(data.shape, (1, 100))
        assert_allclose(data[0].magnitude, [p[0] for p in in_info.grid.points])

    def test_parametric_points_2d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UnstructuredPoints(np.random.random((100, 2))),
            units="m",
        )

        source = fm.components.ParametricGrid(
            info=in_info,
            func=lambda t, x, y: x * y,
        )
        trigger = fm.components.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.components.DebugConsumer(
            {"Input": fm.Info(None, grid=None, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])

        source.outputs["Grid"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"]
        self.assertEqual(data.shape, (1, 100))
        assert_allclose(data[0].magnitude, [p[0] * p[1] for p in in_info.grid.points])

    def test_parametric_points_3d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UnstructuredPoints(np.random.random((100, 3))),
            units="m",
        )

        source = fm.components.ParametricGrid(
            info=in_info,
            func=lambda t, x, y, z: x * y - z,
        )
        trigger = fm.components.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.components.DebugConsumer(
            {"Input": fm.Info(None, grid=None, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])

        source.outputs["Grid"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"]
        self.assertEqual(data.shape, (1, 100))
        assert_allclose(
            data[0].magnitude, [p[0] * p[1] - p[2] for p in in_info.grid.points]
        )

    def test_parametric_fail_nogrid(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.NoGrid(1),
            units="m",
        )

        source = fm.components.ParametricGrid(
            info=in_info,
            func=lambda t, x: x,
        )
        trigger = fm.components.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.components.DebugConsumer(
            {"Input": fm.Info(None, grid=None, units=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])

        source.outputs["Grid"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        with self.assertRaises(fm.FinamMetaDataError):
            composition.connect(time)


class TestStaticParametricGrid(unittest.TestCase):
    def test_static_parametric(self):
        in_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20, 15)),
            units="m",
        )

        source = fm.components.StaticParametricGrid(
            info=in_info,
            func=lambda x, y: x,
        )
        sink = fm.components.DebugPushConsumer(
            inputs={
                "Input": fm.Info(time=None, grid=in_info.grid, units=None),
            },
            log_data="INFO",
        )

        composition = fm.Composition([source, sink])

        source.outputs["Grid"] >> sink.inputs["Input"]

        composition.connect(None)
        data_1 = sink.data["Input"][0, ...]

        self.assertEqual(data_1.shape, (19, 14))

        composition.run(end_time=None)

        data_2 = sink.data["Input"][0, ...]
        assert_allclose(data_1.magnitude, data_2.magnitude)
        self.assertEqual(data_2.shape, (19, 14))


if __name__ == "__main__":
    unittest.main()
