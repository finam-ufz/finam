import unittest
from datetime import datetime

from finam.core.interfaces import ComponentStatus
from finam.core.sdk import Input, IOList, Output
from finam.data import Info, NoGrid
from finam.tools.connect_helper import ConnectHelper


class TestConnectHelper(unittest.TestCase):
    def test_connect(self):
        time = datetime(2020, 10, 6)
        info = Info(grid=NoGrid())

        inputs = IOList("INPUT")
        inputs.add(name="In1")
        inputs.add(name="In2")
        outputs = IOList("OUTPUT")
        outputs.add(name="Out1")
        outputs.add(name="Out2")

        sources = [Output("so1"), Output("so1")]
        sinks = [Input("si1"), Input("si2")]

        sources[0] >> inputs["In1"]
        sources[1] >> inputs["In2"]

        outputs["Out1"] >> sinks[0]
        outputs["Out2"] >> sinks[1]

        connector: ConnectHelper = ConnectHelper(
            inputs,
            outputs,
            required_in_data=list(inputs.keys()),
            required_out_infos=list(outputs.keys()),
        )

        self.assertEqual(connector.infos_pushed, {"Out1": False, "Out2": False})
        self.assertEqual(connector.data_pushed, {"Out1": False, "Out2": False})

        self.assertEqual(connector.in_data, {"In1": None, "In2": None})
        self.assertEqual(connector.in_infos, {"In1": None, "In2": None})
        self.assertEqual(connector.out_infos, {"Out1": None, "Out2": None})

        status = connector.connect(time)

        self.assertEqual(status, ComponentStatus.CONNECTING_IDLE)

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
        sources[1].push_data(2, time)

        status = connector.connect(
            time, exchange_infos={"In2": info.copy()}, push_infos={"Out2": info.copy()}
        )
        self.assertEqual(status, ComponentStatus.CONNECTING)
        self.assertEqual(connector.in_infos, {"In1": info, "In2": info})
        self.assertEqual(connector.in_data, {"In1": 1, "In2": 2})

        sinks[1].exchange_info(info.copy())
        status = connector.connect(time, push_data={"Out1": 1, "Out2": 2})
        self.assertEqual(status, ComponentStatus.CONNECTED)

        self.assertEqual(connector.infos_pushed, {"Out1": True, "Out2": True})
        self.assertEqual(connector.data_pushed, {"Out1": True, "Out2": True})

        self.assertEqual(connector.in_data, {"In1": 1, "In2": 2})
        self.assertEqual(connector.in_infos, {"In1": info, "In2": info})
        self.assertEqual(connector.out_infos, {"Out1": info, "Out2": info})
