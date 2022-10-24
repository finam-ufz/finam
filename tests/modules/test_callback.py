import unittest
from datetime import datetime, timedelta

import numpy as np

from finam import Composition, Info, NoGrid
from finam.modules import CallbackComponent, CallbackGenerator, DebugConsumer


def transform(inputs, _time):
    return {"Out1": inputs["In1"] * 2.0}


def consume(_inputs, _time):
    return {}


class TestCallback(unittest.TestCase):
    def test_callback(self):
        source = CallbackGenerator(
            callbacks={
                "Out1": (
                    lambda t: 1.0 + np.random.random(1)[0],
                    Info(None, grid=NoGrid()),
                )
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )

        trans = CallbackComponent(
            inputs={"In1": Info(None, grid=NoGrid())},
            outputs={"Out1": Info(None, grid=NoGrid())},
            callback=transform,
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )

        consumer = DebugConsumer(
            inputs={"In1": Info(None, grid=NoGrid())},
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )

        composition = Composition([source, trans, consumer])
        composition.initialize()

        _ = source.outputs["Out1"] >> trans.inputs["In1"]
        _ = trans.outputs["Out1"] >> consumer.inputs["In1"]

        composition.connect()

        out_data = consumer.data["In1"]
        self.assertGreaterEqual(out_data, 2.0)
        self.assertLessEqual(out_data, 4.0)

        composition.run(datetime(2000, 3, 1))

        out_data = consumer.data["In1"]
        self.assertGreaterEqual(out_data, 2.0)
        self.assertLessEqual(out_data, 4.0)
