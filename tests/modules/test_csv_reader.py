import unittest
from datetime import datetime
from os import path
from tempfile import TemporaryDirectory

from finam import UNITS, ComponentStatus, Info, Input, NoGrid
from finam.components.readers import CsvReader


class TestCsvReader(unittest.TestCase):
    def test_read_file(self):
        import pandas

        with TemporaryDirectory() as tmp:
            start = datetime(2000, 1, 1)
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
                file,
                time_column="T",
                outputs={"X": "", "Y": "meter"},
                date_format=None,
            )
            sink1 = Input("In1")
            sink2 = Input("In2")

            reader.initialize()

            self.assertEqual(len(reader.outputs), 2)

            reader.outputs["X"] >> sink1
            reader.outputs["Y"] >> sink2

            sink1.ping()
            sink2.ping()

            reader.connect(start)
            reader.connect(start)

            sink1.exchange_info(Info(None, grid=NoGrid(), units=None))
            sink2.exchange_info(Info(None, grid=NoGrid(), units=None))

            reader.outputs["X"].get_info(Info(None, grid=NoGrid(), units=None))
            reader.outputs["Y"].get_info(Info(None, grid=NoGrid(), units=None))

            reader.connect(start)
            reader.connect(start)
            reader.validate()

            self.assertEqual(reader.time, datetime(2000, 1, 1))
            self.assertEqual(
                reader.outputs["X"].get_data(datetime(2000, 1, 1), None), 1
            )
            self.assertEqual(
                reader.outputs["Y"].get_data(datetime(2000, 1, 1), None),
                7 * UNITS.meter,
            )

            self.assertEqual(sink1.info.time, datetime(2000, 1, 1))
            self.assertEqual(sink2.info.time, datetime(2000, 1, 1))

            reader.update()

            self.assertEqual(reader.time, datetime(2000, 1, 2))
            self.assertEqual(
                reader.outputs["X"].get_data(datetime(2000, 1, 2), None), 2
            )
            self.assertEqual(
                reader.outputs["Y"].get_data(datetime(2000, 1, 2), None),
                8 * UNITS.meter,
            )

            reader.update()
            self.assertEqual(reader.time, datetime(2000, 1, 3))

            reader.update()
            self.assertEqual(reader.time, datetime(2000, 1, 5))

            reader.update()
            self.assertEqual(reader.time, datetime(2000, 1, 9))

            reader.update()
            self.assertEqual(reader.time, datetime(2000, 1, 17))

            reader.finalize()
            self.assertEqual(reader.status, ComponentStatus.FINALIZED)


if __name__ == "__main__":
    unittest.main()
