import unittest
from os import path
from tempfile import TemporaryDirectory

from core.interfaces import ComponentStatus
from ..readers import CsvReader


class TestCsvReader(unittest.TestCase):
    def test_read_file(self):
        import pandas

        with TemporaryDirectory() as tmp:
            file = path.join(tmp, "test.csv")

            data = pandas.DataFrame()
            data["T"] = [0, 1, 2, 4, 8, 16]
            data["X"] = [1, 2, 3, 4, 5, 6]
            data["Y"] = [7, 8, 9, 10, 11, 12]

            data.to_csv(file, sep=";", index=False)

            reader = CsvReader(file, time_column="T", outputs=["X", "Y"])

            reader.initialize()

            self.assertEqual(len(reader.outputs()), 2)

            reader.connect()
            reader.validate()

            self.assertEqual(reader.time(), 0)
            self.assertEqual(reader.outputs()["X"].get_data(0), 1)
            self.assertEqual(reader.outputs()["Y"].get_data(0), 7)

            reader.update()

            self.assertEqual(reader.time(), 1)
            self.assertEqual(reader.outputs()["X"].get_data(0), 2)
            self.assertEqual(reader.outputs()["Y"].get_data(0), 8)

            reader.update()
            self.assertEqual(reader.time(), 2)

            reader.update()
            self.assertEqual(reader.time(), 4)

            reader.update()
            self.assertEqual(reader.time(), 8)

            reader.update()
            self.assertEqual(reader.time(), 16)
            self.assertEqual(reader.status(), ComponentStatus.FINISHED)

            with self.assertRaises(AssertionError) as context:
                reader.update()


if __name__ == "__main__":
    unittest.main()
