import copy
import unittest
from datetime import datetime, timedelta

import numpy as np
from numpy.testing import assert_array_equal

import finam as fm
import finam.errors
from finam.components.debug import DebugConsumer
from finam.components.generators import CallbackGenerator, StaticCallbackGenerator
from finam.components.mergers import WeightedSum
from finam.data.tools import Mask


def generate_grid(grid):
    return np.reshape(
        np.random.random(grid.data_size), grid.data_shape, order=grid.order
    )


class TestWeightedSum(unittest.TestCase):
    def test_weighted_sum_simple(self):
        start = datetime(2000, 1, 1)

        value_gen = CallbackGenerator(
            callbacks={
                "A": (
                    lambda t: 1.0,
                    fm.Info(None, grid=fm.NoGrid(), units="mm", mask=Mask.NONE),
                ),
                "B": (
                    lambda t: 2.0,
                    fm.Info(None, grid=fm.NoGrid(), units="mm", mask=Mask.NONE),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )

        weights_gen = StaticCallbackGenerator(
            callbacks={
                "A": (
                    lambda: 0.25,
                    fm.Info(None, grid=fm.NoGrid(), mask=Mask.NONE),
                ),
                "B": (
                    lambda: 0.75,
                    fm.Info(None, grid=fm.NoGrid(), mask=Mask.NONE),
                ),
            }
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([value_gen, weights_gen, merger, consumer])

        value_gen.outputs["A"] >> merger.inputs["In1"]
        weights_gen.outputs["A"] >> merger.inputs["In1_weight"]

        value_gen.outputs["B"] >> merger.inputs["In2"]
        weights_gen.outputs["B"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        composition.run(start_time=start, end_time=start + timedelta(days=30))

        self.assertEqual(consumer.data["WeightedSum"], 1.75 * fm.UNITS.millimeter)
        self.assertEqual(
            fm.data.get_units(consumer.data["WeightedSum"]), fm.UNITS("mm")
        )

    def test_weighted_sum(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((20, 15))

        value_gen = CallbackGenerator(
            callbacks={
                "A": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm", mask=Mask.NONE),
                ),
                "B": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm", mask=Mask.NONE),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )

        weights_gen = StaticCallbackGenerator(
            callbacks={
                "A": (
                    lambda: generate_grid(source_grid),
                    fm.Info(None, source_grid, mask=Mask.NONE),
                ),
                "B": (
                    lambda: generate_grid(source_grid),
                    fm.Info(None, source_grid, mask=Mask.NONE),
                ),
            }
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([value_gen, weights_gen, merger, consumer])

        value_gen.outputs["A"] >> merger.inputs["In1"]
        weights_gen.outputs["A"] >> merger.inputs["In1_weight"]

        value_gen.outputs["B"] >> merger.inputs["In2"]
        weights_gen.outputs["B"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        composition.run(start_time=start, end_time=start + timedelta(days=30))

        self.assertEqual(
            fm.data.get_units(consumer.data["WeightedSum"]), fm.UNITS("mm")
        )

    def test_weighted_sum_fail_grid(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((20, 15))
        source_grid_2 = fm.UniformGrid((20, 10))

        value_gen = CallbackGenerator(
            callbacks={
                "A": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm", mask=Mask.NONE),
                ),
                "B": (
                    lambda t: generate_grid(source_grid_2),
                    fm.Info(None, grid=source_grid_2, units="mm", mask=Mask.NONE),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )

        weights_gen = StaticCallbackGenerator(
            callbacks={
                "A": (
                    lambda: generate_grid(source_grid),
                    fm.Info(None, source_grid, mask=Mask.NONE),
                ),
                "B": (
                    lambda: generate_grid(source_grid_2),
                    fm.Info(None, source_grid_2, mask=Mask.NONE),
                ),
            }
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([value_gen, weights_gen, merger, consumer])

        value_gen.outputs["A"] >> merger.inputs["In1"]
        weights_gen.outputs["A"] >> merger.inputs["In1_weight"]

        value_gen.outputs["B"] >> merger.inputs["In2"]
        weights_gen.outputs["B"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        with self.assertRaises(finam.errors.FinamMetaDataError):
            composition.run(start_time=start, end_time=start + timedelta(days=30))

    def test_weighted_sum_fail_grid_weights(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((20, 15))
        source_grid_2 = fm.UniformGrid((20, 10))

        value_gen = CallbackGenerator(
            callbacks={
                "A": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm", mask=Mask.NONE),
                ),
                "B": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm", mask=Mask.NONE),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )

        weights_gen = StaticCallbackGenerator(
            callbacks={
                "A": (
                    lambda: generate_grid(source_grid),
                    fm.Info(None, source_grid, mask=Mask.NONE),
                ),
                "B": (
                    lambda: generate_grid(source_grid_2),
                    fm.Info(None, source_grid_2, mask=Mask.NONE),
                ),
            }
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([value_gen, weights_gen, merger, consumer])

        value_gen.outputs["A"] >> merger.inputs["In1"]
        weights_gen.outputs["A"] >> merger.inputs["In1_weight"]

        value_gen.outputs["B"] >> merger.inputs["In2"]
        weights_gen.outputs["B"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        with self.assertRaises(finam.errors.FinamMetaDataError):
            composition.run(start_time=start, end_time=start + timedelta(days=30))

    def test_weighted_sum_fail_units(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((20, 15))

        value_gen = CallbackGenerator(
            callbacks={
                "A": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm", mask=Mask.NONE),
                ),
                "B": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="s", mask=Mask.NONE),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )

        weights_gen = StaticCallbackGenerator(
            callbacks={
                "A": (
                    lambda: generate_grid(source_grid),
                    fm.Info(None, source_grid, mask=Mask.NONE),
                ),
                "B": (
                    lambda: generate_grid(source_grid),
                    fm.Info(None, source_grid, mask=Mask.NONE),
                ),
            }
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([value_gen, weights_gen, merger, consumer])

        value_gen.outputs["A"] >> merger.inputs["In1"]
        weights_gen.outputs["A"] >> merger.inputs["In1_weight"]

        value_gen.outputs["B"] >> merger.inputs["In2"]
        weights_gen.outputs["B"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        with self.assertRaises(finam.errors.FinamMetaDataError):
            composition.run(start_time=start, end_time=start + timedelta(days=30))

    def test_weighted_sum_fail_units_weights(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((20, 15))

        value_gen = CallbackGenerator(
            callbacks={
                "A": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm", mask=Mask.NONE),
                ),
                "B": (
                    lambda t: generate_grid(source_grid),
                    fm.Info(None, grid=source_grid, units="mm", mask=Mask.NONE),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )

        weights_gen = StaticCallbackGenerator(
            callbacks={
                "A": (
                    lambda: generate_grid(source_grid),
                    fm.Info(None, source_grid, mask=Mask.NONE),
                ),
                "B": (
                    lambda: generate_grid(source_grid),
                    fm.Info(None, source_grid, units="mm", mask=Mask.NONE),
                ),
            }
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
        )

        composition = fm.Composition([value_gen, weights_gen, merger, consumer])

        value_gen.outputs["A"] >> merger.inputs["In1"]
        weights_gen.outputs["A"] >> merger.inputs["In1_weight"]

        value_gen.outputs["B"] >> merger.inputs["In2"]
        weights_gen.outputs["B"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        with self.assertRaises(finam.errors.FinamMetaDataError):
            composition.run(start_time=start, end_time=start + timedelta(days=30))

    def test_weighted_sum_masked(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((5, 4))

        grid1 = generate_grid(source_grid)
        weights1 = generate_grid(source_grid)
        grid2 = generate_grid(source_grid)
        weights2 = generate_grid(source_grid)

        mask1 = np.full_like(grid1, True, dtype=bool)
        mask1[0, 0] = False
        mask2 = np.full_like(grid2, True, dtype=bool)
        mask1[1, 1] = False

        out_mask = mask1 & mask2
        self.assertFalse(out_mask[0, 0])
        self.assertFalse(out_mask[1, 1])
        self.assertTrue(out_mask[2, 2])

        value_gen = CallbackGenerator(
            callbacks={
                "A": (
                    lambda t: copy.copy(grid1),
                    fm.Info(None, grid=source_grid, units="mm", mask=mask1),
                ),
                "B": (
                    lambda t: copy.copy(grid2),
                    fm.Info(None, grid=source_grid, units="mm", mask=mask2),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )

        weights_gen = StaticCallbackGenerator(
            callbacks={
                "A": (
                    lambda: copy.copy(weights1),
                    fm.Info(None, source_grid, mask=mask1),
                ),
                "B": (
                    lambda: copy.copy(weights2),
                    fm.Info(None, source_grid, mask=mask2),
                ),
            }
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        def debug(name, data, time):
            assert_array_equal(data.mask[0], out_mask)

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
            callbacks={"WeightedSum": debug},
        )

        composition = fm.Composition([value_gen, weights_gen, merger, consumer])

        value_gen.outputs["A"] >> merger.inputs["In1"]
        weights_gen.outputs["A"] >> merger.inputs["In1_weight"]

        value_gen.outputs["B"] >> merger.inputs["In2"]
        weights_gen.outputs["B"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        composition.run(start_time=start, end_time=start + timedelta(days=30))

        self.assertEqual(
            fm.data.get_units(consumer.data["WeightedSum"]), fm.UNITS("mm")
        )

    def test_weighted_sum_masked_submask(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((5, 4))

        grid1 = generate_grid(source_grid)
        weights1 = generate_grid(source_grid)
        grid2 = generate_grid(source_grid)
        weights2 = generate_grid(source_grid)

        mask1 = np.full_like(grid1, True, dtype=bool)
        mask1[0, 0] = False
        mask2 = np.full_like(grid2, True, dtype=bool)
        mask2[1, 1] = False
        weight_mask2 = np.full_like(grid2, True, dtype=bool)
        weight_mask2[1, 1] = False
        weight_mask2[1, 2] = False

        out_mask = mask1 & mask2
        self.assertFalse(out_mask[0, 0])
        self.assertFalse(out_mask[1, 1])
        self.assertTrue(out_mask[2, 2])

        value_gen = CallbackGenerator(
            callbacks={
                "A": (
                    lambda t: copy.copy(grid1),
                    fm.Info(None, grid=source_grid, units="mm", mask=mask1),
                ),
                "B": (
                    lambda t: copy.copy(grid2),
                    fm.Info(None, grid=source_grid, units="mm", mask=mask2),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )

        weights_gen = StaticCallbackGenerator(
            callbacks={
                "A": (
                    lambda: copy.copy(weights1),
                    fm.Info(None, source_grid, mask=Mask.NONE),
                ),
                "B": (
                    lambda: copy.copy(weights2),
                    fm.Info(None, source_grid, mask=weight_mask2),
                ),
            }
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        def debug(name, data, time):
            assert_array_equal(data.mask[0], out_mask)

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
            callbacks={"WeightedSum": debug},
        )

        composition = fm.Composition([value_gen, weights_gen, merger, consumer])

        value_gen.outputs["A"] >> merger.inputs["In1"]
        weights_gen.outputs["A"] >> merger.inputs["In1_weight"]

        value_gen.outputs["B"] >> merger.inputs["In2"]
        weights_gen.outputs["B"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        composition.run(start_time=start, end_time=start + timedelta(days=30))

        self.assertEqual(
            fm.data.get_units(consumer.data["WeightedSum"]), fm.UNITS("mm")
        )

    def test_weighted_sum_masked_fail_submask(self):
        start = datetime(2000, 1, 1)
        source_grid = fm.UniformGrid((5, 4))

        grid1 = generate_grid(source_grid)
        weights1 = generate_grid(source_grid)
        grid2 = generate_grid(source_grid)
        weights2 = generate_grid(source_grid)

        mask1 = np.full_like(grid1, True, dtype=bool)
        mask1[0, 0] = False
        mask2 = np.full_like(grid2, True, dtype=bool)
        mask2[1, 1] = False
        mask2[1, 2] = False
        weight_mask2 = np.full_like(grid2, True, dtype=bool)
        weight_mask2[1, 1] = False

        out_mask = mask1 & mask2
        self.assertFalse(out_mask[0, 0])
        self.assertFalse(out_mask[1, 1])
        self.assertTrue(out_mask[2, 2])

        value_gen = CallbackGenerator(
            callbacks={
                "A": (
                    lambda t: copy.copy(grid1),
                    fm.Info(None, grid=source_grid, units="mm", mask=mask1),
                ),
                "B": (
                    lambda t: copy.copy(grid2),
                    fm.Info(None, grid=source_grid, units="mm", mask=mask2),
                ),
            },
            start=start,
            step=timedelta(days=1),
        )

        weights_gen = StaticCallbackGenerator(
            callbacks={
                "A": (
                    lambda: copy.copy(weights1),
                    fm.Info(None, source_grid, mask=mask1),
                ),
                "B": (
                    lambda: copy.copy(weights2),
                    fm.Info(None, source_grid, mask=weight_mask2),
                ),
            }
        )

        merger = WeightedSum(inputs=["In1", "In2"])

        def debug(name, data, time):
            assert_array_equal(data.mask[0], out_mask)

        consumer = DebugConsumer(
            inputs={"WeightedSum": fm.Info(None, grid=None, units=None)},
            start=start,
            step=timedelta(days=1),
            callbacks={"WeightedSum": debug},
        )

        composition = fm.Composition([value_gen, weights_gen, merger, consumer])

        value_gen.outputs["A"] >> merger.inputs["In1"]
        weights_gen.outputs["A"] >> merger.inputs["In1_weight"]

        value_gen.outputs["B"] >> merger.inputs["In2"]
        weights_gen.outputs["B"] >> merger.inputs["In2_weight"]

        merger.outputs["WeightedSum"] >> consumer.inputs["WeightedSum"]

        with self.assertRaises(finam.errors.FinamMetaDataError):
            composition.run(start_time=start, end_time=start + timedelta(days=30))


if __name__ == "__main__":
    unittest.main()
