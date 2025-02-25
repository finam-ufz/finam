"""
Unit tests for data info propagation.
"""

import unittest
from datetime import datetime, timedelta

from finam import Adapter, Composition, FinamMetaDataError, Info, NoGrid, TimeComponent
from finam.components.generators import CallbackGenerator


class MockupConsumer(TimeComponent):
    def __init__(self, time, info):
        super().__init__()
        self.time = time
        self.step = timedelta(days=1)
        self.info = info
        self.data = None

    def _next_time(self):
        return self.time + self.step

    def _initialize(self):
        self.inputs.add(name="Input", info=self.info)
        self.create_connector()

    def _connect(self, start_time):
        self.try_connect(start_time)

    def _validate(self):
        pass

    def _update(self):
        self.data = self.inputs["Input"].pull_data(self.time, None)
        self.time += self.step

    def _finalize(self):
        pass


class MockupProducer(TimeComponent):
    def __init__(self, time, info):
        super().__init__()
        self.time = time
        self.step = timedelta(days=1)
        self.info = info

        self.out_info = None

    def _next_time(self):
        return self.time + self.step

    def _initialize(self):
        self.outputs.add(name="Output", info=self.info)
        self.create_connector()

    def _connect(self, start_time):
        self.try_connect(start_time, push_data={"Output": 1})
        self.out_info = self.connector.out_infos["Output"]

    def _validate(self):
        pass

    def _update(self):
        self.time += self.step
        self.outputs["Output"].push_data(1, self.time)

    def _finalize(self):
        pass


class SpecAdapter(Adapter):
    def __init__(self):
        super().__init__()

    def _get_data(self, time, target):
        return self.pull_data(time, target)

    def _get_info(self, info):
        in_info = self.exchange_info(info)
        out_info = in_info.copy_with(grid=info.grid)
        return out_info


class TestPropagate(unittest.TestCase):
    def test_propagate_info(self):
        time = datetime(2000, 1, 1)
        source = CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: 1,
                    Info(time=time, grid=NoGrid(), meta={"units": "m"}),
                )
            },
            start=time,
            step=timedelta(days=1),
        )

        sink = MockupConsumer(
            time, Info(time=time, grid=NoGrid(), meta={"units": "km"})
        )

        composition = Composition([source, sink])

        (source.outputs["Output"] >> SpecAdapter() >> sink.inputs["Input"])

        composition.run(end_time=datetime(2000, 1, 2))

        self.assertEqual(
            sink.inputs["Input"].info,
            Info(time=time, grid=NoGrid(), meta={"units": "km"}),
        )

    def test_propagate_info_fail(self):
        time = datetime(2000, 1, 1)
        source = CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: 1,
                    Info(time=time, grid=NoGrid(), meta={"units": "m"}),
                )
            },
            start=time,
            step=timedelta(days=1),
        )

        sink = MockupConsumer(
            time, Info(time=time, grid=NoGrid(), meta={"units": "m**2"})
        )

        composition = Composition([source, sink])

        source.outputs["Output"] >> sink.inputs["Input"]

        with self.assertRaises(FinamMetaDataError):
            composition.run(start_time=time, end_time=datetime(2000, 1, 2))

    def test_propagate_info_from_source(self):
        time = datetime(2000, 1, 1)
        source = CallbackGenerator(
            callbacks={
                "Output": (
                    lambda t: 1,
                    Info(time=time, grid=NoGrid(), meta={"units": "m"}),
                )
            },
            start=time,
            step=timedelta(days=1),
        )

        sink = MockupConsumer(
            datetime(2000, 1, 1), Info(time=None, grid=None, meta={"units": None})
        )

        composition = Composition([source, sink])

        source.outputs["Output"] >> sink.inputs["Input"]

        composition.run(start_time=time, end_time=datetime(2000, 1, 2))

        self.assertEqual(
            sink.inputs["Input"].info,
            Info(time=time, grid=NoGrid(), meta={"units": "m"}),
        )
        self.assertEqual(
            sink.inputs["Input"].info.time,
            time,
        )

    def test_propagate_info_from_target(self):
        time = datetime(2000, 1, 1)
        source = MockupProducer(
            time=datetime(2000, 1, 1),
            info=Info(time=None, grid=None, meta={"units": None}),
        )

        sink = MockupConsumer(
            datetime(2000, 1, 1), Info(time=time, grid=NoGrid(), meta={"units": "m"})
        )

        composition = Composition([source, sink])

        source.outputs["Output"] >> sink.inputs["Input"]

        composition.run(start_time=time, end_time=datetime(2000, 1, 2))

        self.assertEqual(
            source.outputs["Output"].info,
            Info(time=time, grid=NoGrid(), meta={"units": "m"}),
        )
        self.assertEqual(
            source.outputs["Output"].info.time,
            time,
        )
        self.assertEqual(
            source.out_info,
            Info(time=time, grid=NoGrid(), meta={"units": "m"}),
        )
        self.assertEqual(
            source.out_info.time,
            time,
        )


if __name__ == "__main__":
    unittest.main()
