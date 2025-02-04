import unittest
from datetime import datetime

import numpy as np

from finam import ComponentStatus, Info, Input, NoGrid, Output, UniformGrid
from finam.sdk.component import IOList
from finam.tools.connect_helper import ConnectHelper, FromInput, FromOutput, FromValue


class TestConnectHelper(unittest.TestCase):
    def test_connect(self):
        time = datetime(2020, 10, 6)
        info = Info(grid=NoGrid(), time=time)

        inputs = IOList(None, "INPUT")
        inputs.add(name="In1")
        inputs.add(name="In2", grid=NoGrid(), time=time)
        outputs = IOList(None, "OUTPUT")
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
            pull_data=list(inputs.keys()),
            cache=False,
        )
        self.assertEqual(connector.uses_base_logger_name, True)

        self.assertEqual(connector.infos_pushed, {"Out1": False, "Out2": False})
        self.assertEqual(connector.data_pushed, {"Out1": False, "Out2": False})

        self.assertEqual(connector.in_data, {"In1": None, "In2": None})
        self.assertEqual(connector.in_infos, {"In1": None, "In2": None})
        self.assertEqual(connector.out_infos, {"Out1": None, "Out2": None})

        self.assertEqual(connector.data_required, {"Out1": True, "Out2": True})
        self.assertEqual(connector.in_infos_required, {"In1": True, "In2": False})
        self.assertEqual(connector.out_infos_required, {"Out1": True, "Out2": True})

        status = connector.connect(time)

        self.assertEqual(status, ComponentStatus.CONNECTING_IDLE)

        status = connector.connect(time, exchange_infos={"In1": info.copy()})

        sources[0].push_info(info.copy())

        status = connector.connect(time, exchange_infos={"In1": info.copy()})
        self.assertEqual(status, ComponentStatus.CONNECTING)
        self.assertEqual(connector.in_infos, {"In1": info, "In2": None})

        self.assertEqual(connector.data_required, {"Out1": True, "Out2": True})
        self.assertEqual(connector.in_infos_required, {"In1": False, "In2": False})
        self.assertEqual(connector.out_infos_required, {"Out1": True, "Out2": True})

        sources[0].push_data(1, time)

        status = connector.connect(time)
        self.assertEqual(status, ComponentStatus.CONNECTING)
        self.assertEqual(connector.in_data, {"In1": 1, "In2": None})

        status = connector.connect(time)
        self.assertEqual(status, ComponentStatus.CONNECTING_IDLE)

        status = connector.connect(time, push_infos={"Out1": info.copy()})
        self.assertEqual(status, ComponentStatus.CONNECTING)
        self.assertEqual(connector.out_infos, {"Out1": None, "Out2": None})

        self.assertEqual(connector.data_required, {"Out1": True, "Out2": True})
        self.assertEqual(connector.in_infos_required, {"In1": False, "In2": False})
        self.assertEqual(connector.out_infos_required, {"Out1": False, "Out2": True})

        sinks[0].exchange_info(info.copy())

        status = connector.connect(time)
        self.assertEqual(status, ComponentStatus.CONNECTING)
        self.assertEqual(connector.out_infos, {"Out1": info, "Out2": None})

        sources[1].push_info(info.copy())

        status = connector.connect(
            time, exchange_infos={"In2": info.copy()}, push_infos={"Out2": info.copy()}
        )
        sources[1].push_data(2, time)

        self.assertEqual(connector.data_required, {"Out1": True, "Out2": True})
        self.assertEqual(connector.in_infos_required, {"In1": False, "In2": False})
        self.assertEqual(connector.out_infos_required, {"Out1": False, "Out2": False})

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

        self.assertEqual(connector.data_required, {"Out1": False, "Out2": False})

        self.assertEqual(connector.infos_pushed, {"Out1": True, "Out2": True})
        self.assertEqual(connector.data_pushed, {"Out1": True, "Out2": True})

        self.assertEqual(connector.in_data, {"In1": 1, "In2": 2})
        self.assertEqual(connector.in_infos, {"In1": info, "In2": info})
        self.assertEqual(connector.out_infos, {"Out1": info, "Out2": info})

    def test_connect_fail(self):
        time = datetime(2020, 10, 6)

        inputs = IOList(None, "INPUT")
        inputs.add(name="In1")
        inputs.add(name="In2")
        outputs = IOList(None, "OUTPUT")
        outputs.add(name="Out1")
        outputs.add(name="Out2")

        with self.assertRaises(KeyError):
            _connector = ConnectHelper("TestLogger", inputs, outputs, pull_data=["In3"])

        connector = ConnectHelper("TestLogger", inputs, outputs)

        with self.assertRaises(KeyError):
            connector.connect(
                start_time=None, exchange_infos={"In3": Info(time, NoGrid())}
            )
        with self.assertRaises(KeyError):
            connector.connect(
                start_time=None, push_infos={"Out3": Info(time, NoGrid())}
            )
        with self.assertRaises(KeyError):
            connector.connect(start_time=None, push_data={"Out3": 0.0})

    def test_connect_caching(self):
        time = datetime(2020, 10, 6)

        info = Info(grid=NoGrid(), time=time)

        inputs = IOList(None, "INPUT")
        inputs.add(name="In1")
        inputs.add(name="In2")
        outputs = IOList(None, "OUTPUT")
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
            pull_data=list(inputs.keys()),
            cache=True,
        )
        connector.connect(
            time,
            exchange_infos={"In1": info.copy(), "In2": info.copy()},
            push_infos={"Out1": info.copy(), "Out2": info.copy()},
            push_data={"Out1": 1, "Out2": 2},
        )

        sources[0].push_info(info.copy())
        sources[1].push_info(info.copy())

        sinks[0].exchange_info(info.copy())
        sinks[1].exchange_info(info.copy())

        connector.connect(time)

        sources[0].push_data(1, time)
        sources[1].push_data(2, time)

        status = connector.connect(time)

        self.assertEqual(status, ComponentStatus.CONNECTED)

    def test_connect_transfer_from_input(self):
        time = datetime(2020, 10, 6)

        inputs = IOList(None, "INPUT")
        inputs.add(name="In1", time=None, grid=None)
        inputs.add(name="In2", time=None, grid=None, units=None)
        outputs = IOList(None, "OUTPUT")
        outputs.add(name="Out1")

        sources = [Output("so1"), Output("so1")]
        sink = Input("si1")

        sources[0] >> inputs["In1"]
        sources[1] >> inputs["In2"]

        outputs["Out1"] >> sink

        inputs["In1"].ping()
        inputs["In2"].ping()
        sink.ping()

        connector: ConnectHelper = ConnectHelper(
            "TestLogger",
            inputs,
            outputs,
            pull_data=list(inputs.keys()),
            out_info_rules={
                "Out1": [
                    FromInput("In1", ["time", "grid"]),
                    FromInput("In2", ["units"]),
                    FromValue("test_prop", 1),
                    FromValue("time", time),
                ]
            },
            cache=True,
        )
        connector.connect(
            start_time=None,
            push_data={"Out1": np.zeros((9, 9))},
        )

        sources[0].push_info(Info(time=time, grid=UniformGrid((10, 10))))
        sources[1].push_info(Info(time=time, grid=NoGrid(), units="m"))

        connector.connect(start_time=time)

        self.assertEqual(
            connector.in_infos,
            {
                "In1": Info(time=time, grid=UniformGrid((10, 10))),
                "In2": Info(time=time, grid=NoGrid(), units="m"),
            },
        )
        self.assertEqual(connector.out_infos, {"Out1": None})
        self.assertEqual(connector.infos_pushed, {"Out1": False})

        connector.connect(start_time=time)
        self.assertEqual(connector.infos_pushed, {"Out1": True})
        self.assertEqual(connector.out_infos, {"Out1": None})

        sink.exchange_info(Info(time=time, grid=None, units=None))
        connector.connect(start_time=time)

        self.assertEqual(
            connector.out_infos,
            {
                "Out1": Info(
                    time=time, grid=UniformGrid((10, 10)), units="m", test_prop=1
                )
            },
        )

    def test_connect_transfer_from_output(self):
        time = datetime(2020, 10, 6)

        inputs = IOList(None, "INPUT")
        inputs.add(name="In1")
        inputs.add(name="In2")
        outputs = IOList(None, "OUTPUT")
        outputs.add(name="Out1", time=None, grid=None, units=None)

        sources = [Output("so1"), Output("so1")]
        sink = Input("si1")

        sources[0] >> inputs["In1"]
        sources[1] >> inputs["In2"]

        outputs["Out1"] >> sink

        inputs["In1"].ping()
        inputs["In2"].ping()
        sink.ping()

        connector: ConnectHelper = ConnectHelper(
            "TestLogger",
            inputs,
            outputs,
            pull_data=inputs.names,
            cache=True,
        )
        connector.add_in_info_rule("In1", FromOutput("Out1", ["time", "units"]))
        connector.add_in_info_rule("In2", FromOutput("Out1", ["time", "units"]))
        connector.add_in_info_rule("In2", FromValue("grid", NoGrid()))
        connector.add_in_info_rule("In2", FromValue("time", time))
        connector.connect(
            start_time=time,
            push_data={"Out1": np.zeros((9, 9))},
        )

        sink.exchange_info(Info(time=time, grid=UniformGrid((10, 10)), units="m"))
        connector.connect(start_time=time)

        sources[0].push_info(Info(time=time, grid=UniformGrid((10, 10)), units="m"))
        sources[1].push_info(Info(time=time, grid=NoGrid(), units="m"))

        connector.connect(start_time=time)

        self.assertEqual(
            connector.in_infos,
            {
                "In1": Info(time=time, grid=UniformGrid((10, 10)), units="m"),
                "In2": Info(time=time, grid=NoGrid(), units="m"),
            },
        )

        self.assertEqual(
            connector.out_infos,
            {"Out1": Info(time=time, grid=UniformGrid((10, 10)), units="m")},
        )

    def test_connect_constructor_fail(self):
        inputs = IOList(None, "INPUT")
        inputs.add(name="In1")
        outputs = IOList(None, "OUTPUT")
        outputs.add(name="Out1")

        with self.assertRaises(KeyError):
            _connector: ConnectHelper = ConnectHelper(
                "TestLogger",
                inputs,
                outputs,
                in_info_rules={"InX": []},
            )

        with self.assertRaises(KeyError):
            _connector: ConnectHelper = ConnectHelper(
                "TestLogger",
                inputs,
                outputs,
                out_info_rules={"OutX": []},
            )

        with self.assertRaises(KeyError):
            _connector: ConnectHelper = ConnectHelper(
                "TestLogger",
                inputs,
                outputs,
                in_info_rules={"In1": [FromInput("InX", ["grid"])]},
            )

        with self.assertRaises(KeyError):
            _connector: ConnectHelper = ConnectHelper(
                "TestLogger",
                inputs,
                outputs,
                in_info_rules={"In1": [FromOutput("OutX", ["grid"])]},
            )

        with self.assertRaises(TypeError):
            _connector: ConnectHelper = ConnectHelper(
                "TestLogger",
                inputs,
                outputs,
                in_info_rules={"In1": [FromOutput("OutX", "grid")]},
            )

        with self.assertRaises(TypeError):
            _connector: ConnectHelper = ConnectHelper(
                "TestLogger",
                inputs,
                outputs,
                in_info_rules={"In1": [0]},
            )

    def test_connect_rules_fail(self):
        inputs = IOList(None, "INPUT")
        inputs.add(name="In1")
        outputs = IOList(None, "OUTPUT")
        outputs.add(name="Out1")

        connector: ConnectHelper = ConnectHelper(
            "TestLogger",
            inputs,
            outputs,
        )
        connector.add_in_info_rule("In1", FromOutput("Out1"))
        connector.add_out_info_rule("Out1", FromInput("In1"))
        with self.assertRaises(ValueError):
            connector.connect(
                start_time=None, exchange_infos={"In1": Info(time=None, grid=NoGrid())}
            )

        with self.assertRaises(ValueError):
            connector.connect(
                start_time=None, push_infos={"Out1": Info(time=None, grid=NoGrid())}
            )


if __name__ == "__main__":
    unittest.main()
