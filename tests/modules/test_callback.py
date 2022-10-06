import unittest
from datetime import datetime, timedelta

import numpy as np

from finam.core.schedule import Composition
from finam.data import Info
from finam.modules.callback import CallbackComponent
from finam.modules.generators import CallbackGenerator


def transform(inputs, time):
    inp = inputs["In1"]
    return {"Out1": 0.0 if inp is None else inputs["In1"] * 2.0}


def consume(inputs, time):
    return {}


class TestCallback(unittest.TestCase):
    def test_callback(self):
        source = CallbackGenerator(
            callbacks={"Out1": (lambda t: np.random.random(1)[0], Info())},
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )

        trans = CallbackComponent(
            inputs=["In1"],
            outputs={"Out1": Info()},
            callback=transform,
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )

        consumer = CallbackComponent(
            inputs=["In1"],
            outputs={},
            callback=consume,
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )

        composition = Composition([source, trans, consumer])
        composition.initialize()

        _ = source.outputs["Out1"] >> trans.inputs["In1"]
        _ = trans.outputs["Out1"] >> consumer.inputs["In1"]

        composition.run(datetime(2000, 3, 1))
