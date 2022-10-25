import unittest
from datetime import datetime, timedelta

import finam as fm


class TestTimeTrigger(unittest.TestCase):
    def test_time_trigger(self):
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
        composition.run(datetime(2000, 1, 5))

    def test_time_trigger_from_target(self):
        time = datetime(2000, 1, 1)
        out_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20, 15)),
            units="m",
        )

        source = fm.modules.SimplexNoise()
        trigger = fm.modules.TimeTrigger(
            out_info=fm.Info(time=None, grid=None, units=None),
            start=time,
            step=timedelta(days=1),
        )
        sink = fm.modules.DebugConsumer(
            {"Input": out_info},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])
        composition.initialize()

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect()
        composition.run(datetime(2000, 1, 5))

    def test_time_trigger_fail(self):
        time = datetime(2000, 1, 1)

        trigger = fm.modules.TimeTrigger(start=time, step=timedelta(days=1))

        with self.assertRaises(fm.FinamMetaDataError):
            trigger.initialize()
