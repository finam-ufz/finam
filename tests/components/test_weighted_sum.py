import unittest
from datetime import datetime, timedelta

import numpy as np

import finam as fm
import finam.errors
from finam.components.debug import DebugConsumer
from finam.components.generators import CallbackGenerator
from finam.components.mergers import WeightedSum


def generate_grid(grid):
    return np.reshape(
        np.random.random(grid.data_size), newshape=grid.data_shape, order=grid.order
    )


class TestWeightedSum(unittest.TestCase):
    def test_weighted_sum_simple(self):
        start = datetime(2000, 1, 1)

        generator1 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: 1.0,
                    fm.Info(None, grid=fm.NoGrid(), units="mm"),
                ),
                "Weight": (lambda t: 0.25, fm.Info(None, grid=fm.NoGrid())),
            },
            start=start,
            step=timedelta(days=1),
        )
        generator2 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: 2.0,
                    fm.Info(None, grid=fm.NoGrid(), units="mm"),
                ),
                "Weight": (lambda t: 0.75, fm.Info(None, grid=fm.NoGrid())),
            },
            start=start,
            step=timedelta(days=5),
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([generator1, generator2, merger, consumer])

        generator1.outputs["Value"] >> merger.inputs["In1"]
        generator1.outputs["Weight"] >> merger.inputs["In1_weight"]

        generator2.outputs["Value"] >> merger.inputs["In2"]
        generator2.outputs["Weight"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        composition.run(start_time=start, end_time=start + timedelta(days=30))

        self.assertEqual(consumer.data["WeightedSum"], 1.75 * fm.UNITS.millimeter)
        self.assertEqual(
            fm.data.get_units(consumer.data["WeightedSum"]), fm.UNITS("mm")
        )

    def test_weighted_sum(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((20, 15))

        generator1 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm"),
                ),
                "Weight": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, source_grid),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )
        generator2 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm"),
                ),
                "Weight": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, source_grid),
                ),
            },
            start=start,
            step=timedelta(days=5),
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([generator1, generator2, merger, consumer])

        generator1.outputs["Value"] >> merger.inputs["In1"]
        generator1.outputs["Weight"] >> merger.inputs["In1_weight"]

        generator2.outputs["Value"] >> merger.inputs["In2"]
        generator2.outputs["Weight"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        composition.run(start_time=start, end_time=start + timedelta(days=30))

        self.assertEqual(
            fm.data.get_units(consumer.data["WeightedSum"]), fm.UNITS("mm")
        )

    def test_weighted_sum_fail_grid(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((20, 15))
        source_grid_2 = fm.UniformGrid((20, 10))

        generator1 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm"),
                ),
                "Weight": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, source_grid),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )
        generator2 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: generate_grid(source_grid_2),
                    fm.Info(None, grid=source_grid_2, units="mm"),
                ),
                "Weight": (
                    lambda t: generate_grid(source_grid_2),
                    fm.Info(None, source_grid_2),
                ),
            },
            start=start,
            step=timedelta(days=5),
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([generator1, generator2, merger, consumer])

        generator1.outputs["Value"] >> merger.inputs["In1"]
        generator1.outputs["Weight"] >> merger.inputs["In1_weight"]

        generator2.outputs["Value"] >> merger.inputs["In2"]
        generator2.outputs["Weight"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        with self.assertRaises(finam.errors.FinamMetaDataError):
            composition.run(start_time=start, end_time=start + timedelta(days=30))

    def test_weighted_sum_fail_grid_weights(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((20, 15))
        source_grid_2 = fm.UniformGrid((20, 10))

        generator1 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm"),
                ),
                "Weight": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, source_grid),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )
        generator2 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm"),
                ),
                "Weight": (
                    lambda t: generate_grid(source_grid_2),
                    fm.Info(None, source_grid_2),
                ),
            },
            start=start,
            step=timedelta(days=5),
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([generator1, generator2, merger, consumer])

        generator1.outputs["Value"] >> merger.inputs["In1"]
        generator1.outputs["Weight"] >> merger.inputs["In1_weight"]

        generator2.outputs["Value"] >> merger.inputs["In2"]
        generator2.outputs["Weight"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        with self.assertRaises(finam.errors.FinamMetaDataError):
            composition.run(start_time=start, end_time=start + timedelta(days=30))

    def test_weighted_sum_fail_units(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((20, 15))

        generator1 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm"),
                ),
                "Weight": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, source_grid),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )
        generator2 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="s"),
                ),
                "Weight": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, source_grid),
                ),
            },
            start=start,
            step=timedelta(days=5),
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([generator1, generator2, merger, consumer])

        generator1.outputs["Value"] >> merger.inputs["In1"]
        generator1.outputs["Weight"] >> merger.inputs["In1_weight"]

        generator2.outputs["Value"] >> merger.inputs["In2"]
        generator2.outputs["Weight"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        with self.assertRaises(finam.errors.FinamMetaDataError):
            composition.run(start_time=start, end_time=start + timedelta(days=30))

    def test_weighted_sum_fail_units_weights(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((20, 15))

        generator1 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm"),
                ),
                "Weight": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, source_grid),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )
        generator2 = CallbackGenerator(
            callbacks={
                "Value": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm"),
                ),
                "Weight": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, source_grid, units="mm"),
                ),
            },
            start=start,
            step=timedelta(days=5),
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([generator1, generator2, merger, consumer])

        generator1.outputs["Value"] >> merger.inputs["In1"]
        generator1.outputs["Weight"] >> merger.inputs["In1_weight"]

        generator2.outputs["Value"] >> merger.inputs["In2"]
        generator2.outputs["Weight"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        with self.assertRaises(finam.errors.FinamMetaDataError):
            composition.run(start_time=start, end_time=start + timedelta(days=30))


if __name__ == "__main__":
    unittest.main()
