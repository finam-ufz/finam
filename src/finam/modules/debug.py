"""Generic component with arbitrary inputs and extensive debug logging."""
import logging
from datetime import datetime, timedelta

from ..data import tools
from ..sdk import TimeComponent
from ..tools.log_helper import ErrorLogger


class DebugConsumer(TimeComponent):
    """Generic component with arbitrary inputs and extensive debug logging.

    .. code-block:: text

                   +---------------+
      --> [custom] |               |
      --> [custom] | DebugConsumer |
      --> [......] |               |
                   +---------------+

    Examples
    --------

    .. testcode:: constructor

        import datetime as dt
        import finam as fm

        component = fm.modules.DebugConsumer(
            inputs={
                "A": fm.Info(time=None, grid=fm.NoGrid()),
                "B": fm.Info(time=None, grid=fm.NoGrid()),
            },
            start=dt.datetime(2000, 1, 1),
            step=dt.timedelta(days=7),
            log_data="INFO",
            strip_data=False,
        )

    .. testcode:: constructor
        :hide:

        component.initialize()



    Parameters
    ----------
    inputs : dict[str, Info]
        List of input names
    start : datetime.datetime
        Starting time
    step : datetime.timedelta
        Time step
    log_data : int or str or bool, optional
        Log level for printing received data, like "DEBUG" or "INFO".
        Default ``False``, logs nothing.

        ``True`` uses "INFO".
    strip_data : bool, optional
        Strips data before logging. Default ``True``.
    """

    def __init__(self, inputs, start, step, log_data=False, strip_data=True):
        super().__init__()

        with ErrorLogger(self.logger):
            if not isinstance(start, datetime):
                raise ValueError("Start must be of type datetime")
            if not isinstance(step, timedelta):
                raise ValueError("Step must be of type timedelta")

        self._strip_data = strip_data
        self._log_data = None
        if isinstance(log_data, bool):
            if log_data:
                self._log_data = logging.INFO
        else:
            self._log_data = logging.getLevelName(log_data)

        self._input_infos = inputs
        self._step = step
        self._time = start
        self._data = {}

    @property
    def data(self):
        """dict[str, data] : The component's input data from the last time step"""
        return self._data

    @property
    def next_time(self):
        return self.time + self._step

    def _initialize(self):
        for name, info in self._input_infos.items():
            info.time = self.time
            self.inputs.add(name=name, info=info)
        self.create_connector(pull_data=list(self._input_infos.keys()))

    def _connect(self):
        self.try_connect(self._time)
        for name, info in self.connector.in_infos.items():
            if info is not None:
                self.logger.debug("Exchanged input info for %s", name)
        for name, data in self.connector.in_data.items():
            if data is not None:
                self.logger.debug("Pulled input data for %s", name)

                if self._log_data is not None:
                    pdata = tools.strip_data(data) if self._strip_data else data
                    self.logger.log(
                        self._log_data,
                        'Received "%s" - %s: %s',
                        name,
                        self._time,
                        pdata,
                    )

                self._data[name] = data

    def _validate(self):
        pass

    def _update(self):
        self._data = {
            n: self.inputs[n].pull_data(self.time) for n in self._input_infos.keys()
        }
        for name, data in self._data.items():
            if self._log_data is not None:
                pdata = tools.strip_data(data) if self._strip_data else data
                self.logger.log(
                    self._log_data,
                    'Received "%s" - %s: %s',
                    name,
                    self._time,
                    pdata,
                )

        self._time += self._step

    def _finalize(self):
        pass
