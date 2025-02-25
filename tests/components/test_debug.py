import unittest
from datetime import datetime, timedelta

import finam as fm


class TestScheduleLogger(unittest.TestCase):
    def test_schedule_logger(self):
        start = datetime(2000, 1, 1)
        info = fm.Info(time=start, grid=fm.NoGrid())

        module1 = fm.components.CallbackGenerator(
            callbacks={"Out": (lambda t: t.day, info)},
            start=start,
            step=timedelta(days=2),
        )
        module2 = fm.components.CallbackComponent(
            inputs={
                "In": fm.Info(time=None, grid=fm.NoGrid()),
            },
            outputs={
                "Out": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callback=lambda inp, _t: {"Out": inp["In"][0, ...]},
            start=start,
            step=timedelta(days=5),
        )
        module3 = fm.components.CallbackComponent(
            inputs={
                "In": fm.Info(time=None, grid=fm.NoGrid()),
            },
            outputs={
                "Out": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callback=lambda inp, _t: {"Out": inp["In"][0, ...]},
            start=start,
            step=timedelta(days=8),
        )

        schedule = fm.components.ScheduleLogger(
            inputs={
                "M1": True,
                "M2": True,
                "M3": True,
            },
            log_level="DEBUG",
            stdout=True,
        )

        composition = fm.Composition([module1, module2, module3, schedule])

        module1.outputs["Out"] >> fm.adapters.Scale(1.0) >> module2.inputs["In"]
        module2.outputs["Out"] >> fm.adapters.Scale(1.0) >> module3.inputs["In"]

        module1.outputs["Out"] >> schedule.inputs["M1"]
        module2.outputs["Out"] >> schedule.inputs["M2"]
        module3.outputs["Out"] >> schedule.inputs["M3"]

        composition.connect(start)
        composition.run(end_time=datetime(2000, 1, 30))


class TestPushDebugConsumer(unittest.TestCase):
    def test_consumer(self):
        start = datetime(2000, 1, 1)
        info = fm.Info(time=start, grid=fm.NoGrid())

        module1 = fm.components.CallbackGenerator(
            callbacks={"Out": (lambda t: t.day, info)},
            start=start,
            step=timedelta(days=2),
        )
        consumer = fm.components.DebugPushConsumer(
            inputs={
                "In": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callbacks={
                "In": lambda n, d, t: print(t),
            },
            log_data="INFO",
        )

        composition = fm.Composition([module1, consumer])

        module1.outputs["Out"] >> consumer.inputs["In"]

        composition.connect(start)
        self.assertEqual(consumer.data["In"][0, ...], 1)

        composition.run(start_time=start, end_time=datetime(2000, 1, 10))

        self.assertEqual(consumer.data["In"][0, ...], 11)


if __name__ == "__main__":
    unittest.main()
