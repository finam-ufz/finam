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
        composition.run(end_time=datetime(2000, 1, 5))

    def test_time_trigger_from_source(self):
        time = datetime(2000, 1, 1)
        out_info = fm.Info(
            time=None,
            grid=fm.NoGrid(),
            units="m",
        )

        source = fm.components.CallbackGenerator(
            callbacks={
                "Out": (
                    lambda t: t.day,
                    fm.Info(time=None, grid=fm.NoGrid(), units="m"),
                ),
            },
            start=time,
            step=timedelta(days=1),
        )
        trigger = fm.components.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            out_info=None,
            start=None,
            step=timedelta(days=1),
            start_from_input=True,
        )
        sink = fm.components.DebugConsumer(
            {"Input": out_info},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])

        source.outputs["Out"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)

        self.assertEqual(trigger._time, datetime(2000, 1, 1))

        composition.run(end_time=datetime(2000, 1, 5))

    def test_time_trigger_from_source_with_info(self):
        time = datetime(2000, 1, 1)
        out_info = fm.Info(
            time=None,
            grid=fm.NoGrid(),
            units="m",
        )

        source = fm.components.CallbackGenerator(
            callbacks={
                "Out": (
                    lambda t: t.day,
                    fm.Info(time=None, grid=fm.NoGrid(), units="m"),
                ),
            },
            start=time,
            step=timedelta(days=1),
        )
        trigger = fm.components.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            out_info=fm.Info(time=None, grid=None, units=None),
            start=None,
            step=timedelta(days=1),
            start_from_input=True,
        )
        sink = fm.components.DebugConsumer(
            {"Input": out_info},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])

        source.outputs["Out"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)

        self.assertEqual(trigger._time, datetime(2000, 1, 1))

        composition.run(end_time=datetime(2000, 1, 5))

    def test_time_trigger_from_target(self):
        time = datetime(2000, 1, 1)

        out_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20, 15)),
            units="m",
        )

        source = fm.components.SimplexNoise()
        trigger = fm.components.TimeTrigger(
            out_info=fm.Info(time=None, grid=None, units=None),
            start=None,
            step=timedelta(days=1),
            start_from_input=False,
        )
        sink = fm.components.DebugConsumer(
            {"Input": out_info},
            start=time,
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)

        self.assertEqual(trigger._time, datetime(2000, 1, 1))

        composition.run(end_time=datetime(2000, 1, 5))

    def test_time_trigger_from_target_with_info(self):
        time = datetime(2000, 1, 1)

        out_info = fm.Info(
            time=None,
            grid=fm.UniformGrid((20, 15)),
            units="m",
        )

        source = fm.components.SimplexNoise()
        trigger = fm.components.TimeTrigger(
            in_info=out_info.copy_with(),
            out_info=fm.Info(time=None, grid=None, units=None),
            start=None,
            step=timedelta(days=1),
            start_from_input=False,
        )
        sink = fm.components.DebugConsumer(
            {"Input": out_info},
            start=time,
            step=timedelta(days=1),
        )

        composition = fm.Composition([source, trigger, sink])

        source.outputs["Noise"] >> trigger.inputs["In"]
        trigger.outputs["Out"] >> sink.inputs["Input"]

        composition.connect(time)

        self.assertEqual(trigger._time, datetime(2000, 1, 1))

        composition.run(end_time=datetime(2000, 1, 5))

    def test_time_trigger_fail(self):
        time = datetime(2000, 1, 1)

        trigger = fm.components.TimeTrigger(start=time, step=timedelta(days=1))
        with self.assertRaises(fm.FinamMetaDataError):
            trigger.initialize()

        trigger = fm.components.TimeTrigger(
            out_info=fm.Info(time=None, grid=None, units=None),
            start=None,
            step=timedelta(days=1),
            start_from_input=True,
        )
        with self.assertRaises(fm.FinamMetaDataError):
            trigger.initialize()

        trigger = fm.components.TimeTrigger(
            in_info=fm.Info(time=None, grid=None, units=None),
            start=None,
            step=timedelta(days=1),
            start_from_input=False,
        )
        with self.assertRaises(fm.FinamMetaDataError):
            trigger.initialize()


if __name__ == "__main__":
    unittest.main()
