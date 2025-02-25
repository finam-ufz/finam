import unittest
from datetime import datetime, timedelta

import numpy as np

import finam as fm


class TestNoise(unittest.TestCase):
    def test_noise_scalar_0d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.NoGrid(),
            units="m",
        )

        source = fm.components.SimplexNoise(info=in_info)
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

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect()
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"][0, ...]
        self.assertEqual(data.shape, ())

    def test_noise_uniform_1d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20,)),
            units="m",
        )

        source = fm.components.SimplexNoise(info=in_info)
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

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"][0, ...]
        self.assertEqual(data.shape, (19,))

    def test_noise_uniform_2d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20, 15)),
            units="m",
        )

        source = fm.components.SimplexNoise(info=in_info)
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

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"][0, ...]
        self.assertEqual(data.shape, (19, 14))

    def test_noise_uniform_3d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20, 15, 10)),
            units="m",
        )

        source = fm.components.SimplexNoise(info=in_info)
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

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"][0, ...]
        self.assertEqual(data.shape, (19, 14, 9))

    def test_noise_points_1d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UnstructuredPoints(np.random.random((100, 1))),
            units="m",
        )

        source = fm.components.SimplexNoise(info=in_info)
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

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"][0, ...]
        self.assertEqual(data.shape, (100,))

    def test_noise_points_2d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UnstructuredPoints(np.random.random((100, 2))),
            units="m",
        )

        source = fm.components.SimplexNoise(info=in_info)
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

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"][0, ...]
        self.assertEqual(data.shape, (100,))

    def test_noise_points_3d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UnstructuredPoints(np.random.random((100, 3))),
            units="m",
        )

        source = fm.components.SimplexNoise(info=in_info)
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

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 1, 2))

        data = sink.data["Input"][0, ...]
        self.assertEqual(data.shape, (100,))

    def test_noise_fail_nogrid(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.NoGrid(1),
            units="m",
        )

        source = fm.components.SimplexNoise(info=in_info)
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

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        with self.assertRaises(fm.FinamMetaDataError):
            composition.connect(time)

    def test_noise_fail(self):
        with self.assertRaises(ValueError):
            _source = fm.components.SimplexNoise(octaves=0)

        source = fm.components.SimplexNoise(octaves=1)
        source._update()


class TestStaticNoise(unittest.TestCase):
    def test_static_noise(self):
        in_info = fm.Info(
            time=None,
            grid=fm.NoGrid(),
            units="m",
        )

        source = fm.components.StaticSimplexNoise(info=in_info, seed=123)
        """
        sink = fm.components.DebugConsumer(
            {"Input": fm.Info(None, grid=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        """
        # We want to get to a point where this works
        sink = fm.components.DebugPushConsumer(
            inputs={
                "Input": fm.Info(time=None, grid=fm.NoGrid(), units="m"),
            },
            log_data="INFO",
        )

        composition = fm.Composition([source, sink])

        source.outputs["Noise"] >> sink.inputs["Input"]

        composition.connect(None)
        data_1 = sink.data["Input"][0, ...]

        self.assertEqual(data_1.shape, ())

        composition.run(end_time=None)

        data_2 = sink.data["Input"][0, ...]
        self.assertEqual(data_1, data_2)
        self.assertEqual(data_2.shape, ())


if __name__ == "__main__":
    unittest.main()
