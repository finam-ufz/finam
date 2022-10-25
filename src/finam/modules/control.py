"""Components for controlling data flow"""

from ..data.tools import strip_data
from ..errors import FinamMetaDataError
from ..sdk import TimeComponent
from ..tools.log_helper import ErrorLogger


class TimeTrigger(TimeComponent):
    """Component to forward data in regular time intervals.

    Can be used to enable coupling of pull-based source and push-based target components,
    that would not work due to the dead link otherwise.

    .. code-block:: text

                 +-------------+
                 |             |
        --> [In] | TimeTrigger | [Out] -->
                 |             |
                 +-------------+

    Parameters
    ----------
    start : datetime.datetime
        Starting time
    start : datetime.timedelta
        Time step
    in_info : Info, optional
        Input info, optional. However, one of ``in_info`` or ``out_info`` must be given
    out_info : Info, optional
        Output info, optional. However, one of ``in_info`` or ``out_info`` must be given
    """

    def __init__(self, start, step, in_info=None, out_info=None):
        super().__init__()

        self._ini_in_info = in_info
        self._ini_out_info = out_info

        self._in_info = None
        self._out_info = None

        self.time = start
        self._step = step

    def _initialize(self):
        if self._ini_in_info is None and self._ini_out_info is None:
            with ErrorLogger(self.logger):
                raise FinamMetaDataError(
                    "At least one of input or output info must be given."
                )

        if self._ini_in_info is not None:
            self._ini_in_info.time = self.time
        if self._ini_out_info is not None:
            self._ini_out_info.time = self.time

        self.inputs.add(name="In", info=self._ini_in_info)
        self.outputs.add(name="Out", info=self._ini_out_info)

        self.create_connector(pull_data=["In"])

    def _connect(self):
        in_infos = {}
        out_infos = {}

        if self._ini_out_info is None:
            in_info = self.connector.in_infos["In"]
            if in_info is not None:
                self._in_info = in_info
                self._out_info = in_info
                out_infos["Out"] = self._out_info

        if self._ini_in_info is None:
            out_info = self.connector.out_infos["Out"]
            if out_info is not None:
                self._in_info = out_info
                self._out_info = out_info
                in_infos["In"] = self._in_info

        out_data = {}
        if (
            not self.connector.data_pushed["Out"]
            and self.connector.in_data["In"] is not None
        ):
            out_data["Out"] = self.connector.in_data["In"]

        self.try_connect(
            self.time, exchange_infos=in_infos, push_infos=out_infos, push_data=out_data
        )

    def _validate(self):
        pass

    def _update(self):
        data = strip_data(self.inputs["In"].pull_data(self.time))

        self.time += self._step

        self.outputs["Out"].push_data(data, self.time)

    def _finalize(self):
        pass
