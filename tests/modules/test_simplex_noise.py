import unittest
from datetime import datetime, timedelta

import numpy as np

import finam as fm


class TestSimplexNoise(unittest.TestCase):
    def test_simplex_uniform(self):
        grid = fm.UniformGrid((25, 15))

        source = fm.modules.SimplexNoise()

        consumer = fm.modules.DebugConsumer(
            inputs={"Noise": fm.Info(None, grid=grid, units="")},
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )

        composition = fm.Composition([source, consumer])
        composition.initialize()

        _ = source.outputs["Noise"] >> consumer.inputs["Noise"]

        composition.connect()

        composition.run(datetime(2000, 3, 1))

        print(consumer.data["Noise"])

    def test_simplex_unstructured(self):
        grid = fm.UnstructuredPoints(np.random.random((100, 2)))

        source = fm.modules.SimplexNoise()

        consumer = fm.modules.DebugConsumer(
            inputs={"Noise": fm.Info(None, grid=grid, units="")},
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )

        composition = fm.Composition([source, consumer])
        composition.initialize()

        _ = source.outputs["Noise"] >> consumer.inputs["Noise"]

        composition.connect()

        composition.run(datetime(2000, 3, 1))

        print(consumer.data["Noise"])
