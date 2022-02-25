import unittest
from datetime import datetime
from os import path
from tempfile import TemporaryDirectory

from finam.core.interfaces import ComponentStatus
from finam.core.sdk import FinamStatusError
from finam.modules.readers import CsvReader


class TestCsvReader(unittest.TestCase):
    def test_read_file(self):
        import pandas

        with TemporaryDirectory() as tmp:
            file = path.join(tmp, "test.csv")

            data = pandas.DataFrame()
            data["T"] = [
                "2000-01-01",
                "2000-01-02",
                "2000-01-03",
                "2000-01-05",
                "2000-01-09",
                "2000-01-17",
            ]
            data["X"] = [1, 2, 3, 4, 5, 6]
            data["Y"] = [7, 8, 9, 10, 11, 12]

            data.to_csv(file, sep=";", index=False)

            reader = CsvReader(
                file, time_column="T", date_format=None, outputs=["X", "Y"]
            )

            reader.initialize()

            self.assertEqual(len(reader.outputs), 2)

            reader.connect()
            reader.validate()

            self.assertEqual(reader.time, datetime(2000, 1, 1))
            self.assertEqual(reader.outputs["X"].get_data(datetime(2000, 1, 1)), 1)
            self.assertEqual(reader.outputs["Y"].get_data(datetime(2000, 1, 1)), 7)

            reader.update()

            self.assertEqual(reader.time, datetime(2000, 1, 2))
            self.assertEqual(reader.outputs["X"].get_data(datetime(2000, 1, 2)), 2)
            self.assertEqual(reader.outputs["Y"].get_data(datetime(2000, 1, 2)), 8)

            reader.update()
            self.assertEqual(reader.time, datetime(2000, 1, 3))

            reader.update()
            self.assertEqual(reader.time, datetime(2000, 1, 5))

            reader.update()
            self.assertEqual(reader.time, datetime(2000, 1, 9))

            reader.update()
            self.assertEqual(reader.time, datetime(2000, 1, 17))
            self.assertEqual(reader.status, ComponentStatus.FINISHED)

            with self.assertRaises(FinamStatusError) as context:
                reader.update()


if __name__ == "__main__":
    unittest.main()
