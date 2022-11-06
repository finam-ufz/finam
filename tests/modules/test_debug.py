import unittest
from datetime import datetime, timedelta

import finam as fm


class TestScheduleLogger(unittest.TestCase):
    def test_schedule_logger(self):
        start = datetime(2000, 1, 1)
        info = fm.Info(time=start, grid=fm.NoGrid())

        module1 = fm.modules.CallbackGenerator(
            callbacks={"Out": (lambda t: t.day, info)},
            start=start,
            step=timedelta(days=2),
        )
        module2 = fm.modules.CallbackComponent(
            inputs={
                "In": fm.Info(time=None, grid=fm.NoGrid()),
            },
            outputs={
                "Out": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callback=lambda inp, _t: {"Out": fm.data.strip_data(inp["In"])},
            start=start,
            step=timedelta(days=5),
        )
        module3 = fm.modules.CallbackComponent(
            inputs={
                "In": fm.Info(time=None, grid=fm.NoGrid()),
            },
            outputs={
                "Out": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callback=lambda inp, _t: {"Out": fm.data.strip_data(inp["In"])},
            start=start,
            step=timedelta(days=8),
        )

        schedule = fm.modules.ScheduleLogger(["M1", "M2", "M3"])

        composition = fm.Composition([module1, module2, module3, schedule])
        composition.initialize()

        module1.outputs["Out"] >> fm.adapters.Scale(1.0) >> module2.inputs["In"]
        module2.outputs["Out"] >> fm.adapters.Scale(1.0) >> module3.inputs["In"]

        module1.outputs["Out"] >> schedule.inputs["M1"]
        module2.outputs["Out"] >> schedule.inputs["M2"]
        module3.outputs["Out"] >> schedule.inputs["M3"]

        composition.connect()
        composition.run(datetime(2000, 1, 2))
