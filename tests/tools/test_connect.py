import logging
import unittest
from datetime import datetime

from finam import ComponentStatus, Info, Input, NoGrid, Output
from finam.sdk.component import IOList
from finam.tools.connect_helper import ConnectHelper


class TestConnectHelper(unittest.TestCase):
    def test_connect(self):
        time = datetime(2020, 10, 6)
        info = Info(grid=NoGrid())

        inputs = IOList("INPUT")
        inputs.add(name="In1")
        inputs.add(name="In2", grid=NoGrid())
        outputs = IOList("OUTPUT")
        outputs.add(name="Out1")
        outputs.add(name="Out2")

        sources = [Output("so1"), Output("so1")]
        sinks = [Input("si1"), Input("si2")]

        sources[0] >> inputs["In1"]
        sources[1] >> inputs["In2"]

        outputs["Out1"] >> sinks[0]
        outputs["Out2"] >> sinks[1]

        inputs["In1"].ping()
        inputs["In2"].ping()
        sinks[0].ping()
        sinks[1].ping()

        connector: ConnectHelper = ConnectHelper(
            "TestLogger",
            inputs,
            outputs,
            required_in_data=list(inputs.keys()),
            required_out_infos=list(outputs.keys()),
        )
        self.assertEqual(connector.uses_base_logger_name, True)

        self.assertEqual(connector.infos_pushed, {"Out1": False, "Out2": False})
        self.assertEqual(connector.data_pushed, {"Out1": False, "Out2": False})

        self.assertEqual(connector.in_data, {"In1": None, "In2": None})
        self.assertEqual(connector.in_infos, {"In1": None, "In2": None})
        self.assertEqual(connector.out_infos, {"Out1": None, "Out2": None})

        status = connector.connect(time)

        self.assertEqual(status, ComponentStatus.CONNECTING_IDLE)

        status = connector.connect(time, exchange_infos={"In1": info.copy()})

        sources[0].push_info(info.copy())

        status = connector.connect(time, exchange_infos={"In1": info.copy()})
        self.assertEqual(status, ComponentStatus.CONNECTING)
        self.assertEqual(connector.in_infos, {"In1": info, "In2": None})

        sources[0].push_data(1, time)

        status = connector.connect(time)
        self.assertEqual(status, ComponentStatus.CONNECTING)
        self.assertEqual(connector.in_data, {"In1": 1, "In2": None})

        status = connector.connect(time)
        self.assertEqual(status, ComponentStatus.CONNECTING_IDLE)

        status = connector.connect(time, push_infos={"Out1": info.copy()})
        self.assertEqual(status, ComponentStatus.CONNECTING)
        self.assertEqual(connector.out_infos, {"Out1": None, "Out2": None})

        sinks[0].exchange_info(info.copy())

        status = connector.connect(time)
        self.assertEqual(status, ComponentStatus.CONNECTING)
        self.assertEqual(connector.out_infos, {"Out1": info, "Out2": None})

        sources[1].push_info(info.copy())

        status = connector.connect(
            time, exchange_infos={"In2": info.copy()}, push_infos={"Out2": info.copy()}
        )
        sources[1].push_data(2, time)

        self.assertEqual(status, ComponentStatus.CONNECTING)
        self.assertEqual(connector.in_infos, {"In1": info, "In2": info})

        connector.connect(
            time, exchange_infos={"In2": info.copy()}, push_infos={"Out2": info.copy()}
        )

        self.assertEqual(connector.in_data["In1"], 1)
        self.assertEqual(connector.in_data["In2"], 2)

        sinks[1].exchange_info(info.copy())
        status = connector.connect(time, push_data={"Out1": 1, "Out2": 2})
        self.assertEqual(status, ComponentStatus.CONNECTED)

        self.assertEqual(connector.infos_pushed, {"Out1": True, "Out2": True})
        self.assertEqual(connector.data_pushed, {"Out1": True, "Out2": True})

        self.assertEqual(connector.in_data, {"In1": 1, "In2": 2})
        self.assertEqual(connector.in_infos, {"In1": info, "In2": info})
        self.assertEqual(connector.out_infos, {"Out1": info, "Out2": info})

    def test_connect_fail(self):
        inputs = IOList("INPUT")
        inputs.add(name="In1")
        inputs.add(name="In2")
        outputs = IOList("OUTPUT")
        outputs.add(name="Out1")
        outputs.add(name="Out2")

        with self.assertRaises(ValueError):
            _connector = ConnectHelper(
                "TestLogger", inputs, outputs, required_in_data=["In3"]
            )

        with self.assertRaises(ValueError):
            _connector = ConnectHelper(
                "TestLogger", inputs, outputs, required_out_infos=["Out3"]
            )

        connector = ConnectHelper("TestLogger", inputs, outputs)

        with self.assertRaises(ValueError):
            connector.connect(time=None, exchange_infos={"In3": Info(NoGrid())})
        with self.assertRaises(ValueError):
            connector.connect(time=None, push_infos={"Out3": Info(NoGrid())})
        with self.assertRaises(ValueError):
            connector.connect(time=None, push_data={"Out3": 0.0})
