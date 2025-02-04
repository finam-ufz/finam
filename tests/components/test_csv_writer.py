import unittest
from datetime import datetime, timedelta
from os import path
from tempfile import TemporaryDirectory

from numpy.testing import assert_array_equal

from finam import Composition, Info, NoGrid
from finam.components.generators import CallbackGenerator
from finam.components.writers import CsvWriter


class TestCsvWriter(unittest.TestCase):
    def test_write_file(self):
        import pandas as pd

        with TemporaryDirectory() as tmp:
            file_path = path.join(tmp, "test.csv")
            start = datetime(2000, 1, 1)

            generator = CallbackGenerator(
                callbacks={
                    "A": (lambda t: 0, Info(None, grid=NoGrid())),
                    "B": (lambda t: (t - start).days, Info(None, grid=NoGrid())),
                    "C": (lambda t: (t - start).days * 2, Info(None, grid=NoGrid())),
                },
                start=start,
                step=timedelta(days=1),
            )

            writer = CsvWriter(
                inputs=["A", "B", "C"],
                path=file_path,
                start=start,
                step=timedelta(days=1),
                separator=",",
            )

            comp = Composition([generator, writer])

            generator.outputs["A"] >> writer.inputs["A"]
            generator.outputs["B"] >> writer.inputs["B"]
            generator.outputs["C"] >> writer.inputs["C"]

            comp.run(start_time=start, end_time=datetime(2000, 1, 31))

            csv = pd.read_csv(file_path)

            assert_array_equal(csv.columns, ["time", "A", "B", "C"])
            assert_array_equal(csv["B"], list(range(0, 31)))
            self.assertEqual(csv.shape[0], 31)

    def test_constructor_fail(self):
        with self.assertRaises(ValueError):
            _writer = CsvWriter(
                inputs=["A", "B", "C"],
                path="abc",
                start=0,
                step=timedelta(days=1),
                separator=",",
            )

        with self.assertRaises(ValueError):
            _writer = CsvWriter(
                inputs=["A", "B", "C"],
                path="abc",
                start=datetime(2000, 1, 1),
                step=1,
                separator=",",
            )


if __name__ == "__main__":
    unittest.main()
