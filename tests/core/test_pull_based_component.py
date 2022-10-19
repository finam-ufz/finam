import unittest
from datetime import datetime, timedelta
from functools import partial

import finam as fm
from finam.modules.debug import DebugConsumer


class PullComponent(fm.AComponent):
    def __init__(self):
        super().__init__()

    def _initialize(self):
        self.outputs.add(
            fm.CallbackOutput(
                callback=partial(self._get_data, "Out"), name="Out", grid=fm.NoGrid()
            )
        )
        self.create_connector()

    def _connect(self):
        self.try_connect()

    def _validate(self):
        pass

    def _update(self):
        pass

    def _finalize(self):
        pass

    def _get_data(self, _name, _caller, time):
        return time.day


class TestPullBasedComponent(unittest.TestCase):
    def test_component(self):
        time = datetime(2000, 1, 1)

        pull_comp = PullComponent()
        consumer = DebugConsumer(
            inputs={"In": fm.Info(grid=fm.NoGrid())}, start=time, step=timedelta(days=1)
        )

        composition = fm.Composition([pull_comp, consumer], log_level="DEBUG")
        composition.initialize()

        pull_comp.outputs["Out"] >> consumer.inputs["In"]

        composition.run(t_max=datetime(2000, 1, 12))

        self.assertEqual(consumer.data, {"In": 11})
