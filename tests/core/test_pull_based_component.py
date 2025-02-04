import unittest
from datetime import datetime, timedelta
from functools import partial

import finam as fm
from finam.components.debug import DebugConsumer


class PullComponent(fm.Component):
    def __init__(self):
        super().__init__()

    def _initialize(self):
        self.outputs.add(
            fm.CallbackOutput(
                callback=partial(self._get_data, "Out"),
                name="Out",
                time=None,
                grid=fm.NoGrid(),
            )
        )
        self.create_connector()

    def _connect(self, start_time):
        self.try_connect(start_time)

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
            inputs={"In": fm.Info(time=time, grid=fm.NoGrid())},
            start=time,
            step=timedelta(days=1),
        )

        composition = fm.Composition([pull_comp, consumer], log_level="DEBUG")

        pull_comp.outputs["Out"] >> consumer.inputs["In"]

        composition.run(start_time=time, end_time=datetime(2000, 1, 12))

        self.assertEqual(consumer.data, {"In": 12})


if __name__ == "__main__":
    unittest.main()
