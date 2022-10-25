import unittest
from datetime import datetime, timedelta

import numpy as np

import finam as fm


class TestSimplexNoise(unittest.TestCase):
    def test_simplex_uniform(self):
        grid = fm.UniformGrid((25, 15), origin=(10.0, 5.0))

        source = fm.modules.SimplexNoise(octaves=3, frequency=0.01, seed=4)

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
        grid = fm.UnstructuredPoints(np.random.random((100, 2)) * 100)

        source = fm.modules.SimplexNoise(octaves=3, frequency=0.01, seed=4)

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
