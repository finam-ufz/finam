import unittest
from datetime import datetime, timedelta

import numpy as np

import finam as fm


class TestNoise(unittest.TestCase):
    def test_noise_uniform_1d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20,)),
            units="m",
        )

        source = fm.modules.SimplexNoise(info=in_info)
        trigger = fm.modules.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.modules.DebugConsumer(
            {"Input": fm.Info(None, grid=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])
        composition.initialize()

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect()
        composition.run(datetime(2000, 1, 2))

        data = fm.data.strip_data(sink.data["Input"])
        self.assertEqual(data.shape, (19,))

    def test_noise_uniform_2d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20, 15)),
            units="m",
        )

        source = fm.modules.SimplexNoise(info=in_info)
        trigger = fm.modules.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.modules.DebugConsumer(
            {"Input": fm.Info(None, grid=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])
        composition.initialize()

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect()
        composition.run(datetime(2000, 1, 2))

        data = fm.data.strip_data(sink.data["Input"])
        self.assertEqual(data.shape, (19, 14))

    def test_noise_uniform_3d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20, 15, 10)),
            units="m",
        )

        source = fm.modules.SimplexNoise(info=in_info)
        trigger = fm.modules.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.modules.DebugConsumer(
            {"Input": fm.Info(None, grid=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])
        composition.initialize()

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect()
        composition.run(datetime(2000, 1, 2))

        data = fm.data.strip_data(sink.data["Input"])
        self.assertEqual(data.shape, (19, 14, 9))

    def test_noise_points_1d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UnstructuredPoints(np.random.random((100, 1))),
            units="m",
        )

        source = fm.modules.SimplexNoise(info=in_info)
        trigger = fm.modules.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.modules.DebugConsumer(
            {"Input": fm.Info(None, grid=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])
        composition.initialize()

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect()
        composition.run(datetime(2000, 1, 2))

        data = fm.data.strip_data(sink.data["Input"])
        self.assertEqual(data.shape, (100,))

    def test_noise_points_2d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UnstructuredPoints(np.random.random((100, 2))),
            units="m",
        )

        source = fm.modules.SimplexNoise(info=in_info)
        trigger = fm.modules.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.modules.DebugConsumer(
            {"Input": fm.Info(None, grid=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])
        composition.initialize()

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect()
        composition.run(datetime(2000, 1, 2))

        data = fm.data.strip_data(sink.data["Input"])
        self.assertEqual(data.shape, (100,))

    def test_noise_points_3d(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.UnstructuredPoints(np.random.random((100, 3))),
            units="m",
        )

        source = fm.modules.SimplexNoise(info=in_info)
        trigger = fm.modules.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.modules.DebugConsumer(
            {"Input": fm.Info(None, grid=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])
        composition.initialize()

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect()
        composition.run(datetime(2000, 1, 2))

        data = fm.data.strip_data(sink.data["Input"])
        self.assertEqual(data.shape, (100,))

    def test_noise_fail_nogrid(self):
        time = datetime(2000, 1, 1)
        in_info = fm.Info(
            time=None,
            grid=fm.NoGrid(),
            units="m",
        )

        source = fm.modules.SimplexNoise(info=in_info)
        trigger = fm.modules.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.modules.DebugConsumer(
            {"Input": fm.Info(None, grid=None)},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])
        composition.initialize()

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        with self.assertRaises(fm.FinamMetaDataError):
            composition.connect()

    def test_noise_fail(self):
        with self.assertRaises(ValueError):
            _source = fm.modules.SimplexNoise(octaves=0)

        source = fm.modules.SimplexNoise(octaves=1)
        source._update()
