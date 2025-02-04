import unittest
from datetime import datetime, timedelta

import numpy as np

import finam as fm
from finam import Composition, Info, NoGrid
from finam.components import DebugPushConsumer, StaticCallbackGenerator


def consume(_inputs, _time):
    return {}


class TestStaticCallbackGenerator(unittest.TestCase):
    def test_static_callback(self):
        source = StaticCallbackGenerator(
            callbacks={
                "Out1": (
                    lambda: 1.0 + np.random.random(1)[0],
                    Info(None, grid=NoGrid()),
                )
            },
        )
        consumer = DebugPushConsumer(
            inputs={"In1": Info(None, grid=NoGrid())},
            log_data="DEBUG",
        )

        composition = Composition([source, consumer])

        _ = source.outputs["Out1"] >> fm.adapters.Scale(2.0) >> consumer.inputs["In1"]

        composition.connect(None)

        out_data_1 = consumer.data["In1"]

        self.assertGreaterEqual(out_data_1, 2.0)
        self.assertLessEqual(out_data_1, 4.0)

        composition.run()

        out_data_2 = consumer.data["In1"]
        self.assertEqual(out_data_1, out_data_2)


if __name__ == "__main__":
    unittest.main()
