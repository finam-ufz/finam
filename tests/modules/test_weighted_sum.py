import unittest
from datetime import datetime, timedelta

import numpy as np

import finam as fm
from finam.modules.debug import DebugConsumer
from finam.modules.generators import CallbackGenerator
from finam.modules.mergers import WeightedSum


def generate_grid(grid):
    return np.reshape(
        np.random.random(grid.data_size), newshape=grid.data_shape, order=grid.order
    )


class TestWeightedSum(unittest.TestCase):
    def test_weighted_sum(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((20, 15))

        generator1 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(grid=source_grid, units="mm"),
                ),
                "Weight": (lambda t: generate_grid(source_grid), fm.Info(source_grid)),
            },
            start=start,
            step=timedelta(days=1),
        )
        generator2 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(grid=source_grid, units="mm"),
                ),
                "Weight": (lambda t: generate_grid(source_grid), fm.Info(source_grid)),
            },
            start=start,
            step=timedelta(days=5),
        )

        merger = WeightedSum(inputs=["In1", "In2"], start=start)

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(grid=source_grid, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([generator1, generator2, merger, consumer])
        composition.initialize()

        generator1.outputs["Value"] >> merger.inputs["In1"]
        generator1.outputs["Weight"] >> merger.inputs["In1_weight"]

        generator2.outputs["Value"] >> merger.inputs["In2"]
        generator2.outputs["Weight"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        composition.run(t_max=start + timedelta(days=30))
