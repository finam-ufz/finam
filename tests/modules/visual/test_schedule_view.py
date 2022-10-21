import unittest
from datetime import datetime, timedelta

from finam import Composition, Info, NoGrid
from finam.modules.generators import CallbackGenerator
from finam.modules.visual.schedule import ScheduleView


class TestSchedule(unittest.TestCase):
    def test_schedule(self):
        start = datetime(2000, 1, 1)

        gen1 = CallbackGenerator(
            callbacks={"Out": (lambda t: 0, Info(None, grid=NoGrid()))},
            start=start,
            step=timedelta(days=1),
        )
        gen2 = CallbackGenerator(
            callbacks={"Out": (lambda t: 0, Info(None, grid=NoGrid()))},
            start=start,
            step=timedelta(days=3),
        )

        schedule = ScheduleView(["Gen1", "Gen2"])

        comp = Composition([gen1, gen2, schedule])
        comp.initialize()

        gen1.outputs["Out"] >> schedule.inputs["Gen1"]
        gen2.outputs["Out"] >> schedule.inputs["Gen2"]

        comp.run(t_max=datetime(2000, 1, 15))
