import unittest
from datetime import datetime, timedelta

import numpy as np

import finam as fm


class TestSimplexNoise(unittest.TestCase):
    def test_simplex_uniform(self):
        time = datetime(2000, 1, 1)
        grid = fm.UniformGrid((25, 15), origin=(10.0, 5.0))

        source = fm.components.SimplexNoise(octaves=3, frequency=0.01, seed=4)

        consumer = fm.components.DebugConsumer(
            inputs={"Noise": fm.Info(None, grid=grid, units="")},
            start=time,
            step=timedelta(days=7),
        )

        composition = fm.Composition([source, consumer])

        _ = source.outputs["Noise"] >> consumer.inputs["Noise"]

        composition.connect(time)

        composition.run(end_time=datetime(2000, 3, 1))

        print(consumer.data["Noise"])

    def test_simplex_unstructured(self):
        time = datetime(2000, 1, 1)
        grid = fm.UnstructuredPoints(np.random.random((100, 2)) * 100)

        source = fm.components.SimplexNoise(octaves=3, frequency=0.01, seed=4)

        consumer = fm.components.DebugConsumer(
            inputs={"Noise": fm.Info(None, grid=grid, units="")},
            start=time,
            step=timedelta(days=7),
        )

        composition = fm.Composition([source, consumer])

        _ = source.outputs["Noise"] >> consumer.inputs["Noise"]

        composition.connect(time)
        composition.run(end_time=datetime(2000, 3, 1))

        print(consumer.data["Noise"])


if __name__ == "__main__":
    unittest.main()
