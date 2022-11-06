"""Generic component with arbitrary inputs and extensive debug logging."""
import logging
from datetime import datetime, timedelta

from ..data import tools
from ..interfaces import ComponentStatus, IInput
from ..sdk import CallbackInput, Component, TimeComponent
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
        self._time += self._step

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

    def _finalize(self):
        pass


class ScheduleLogger(Component):

    """Logging of module update schedule.

    Takes inputs of arbitrary types and simply logs the time of notifications of each input
    as an ASCII graph.

    .. code-block:: text

                     +----------------+
        --> [custom] |                |
        --> [custom] | ScheduleLogger |
        --> [......] |                |
                     +----------------+

    Note:
        This component is push-based without an internal time step.

    Examples
    --------

    .. testcode:: constructor

        from datetime import timedelta
        import finam as fm

        schedule = fm.modules.ScheduleLogger(
            inputs={"Grid1": True, "Grid2": True},
            time_step=timedelta(days=1),
            log_level="INFO",
        )

    .. testcode:: constructor
        :hide:

        schedule.initialize()

    Parameters
    ----------
    inputs : dict of str, bool
        Input names and whether to pull data from them when notified.
        Pulling is useful for correct output behaviour when clearing the data cache.
    time_step : datetime.timedelta, optional
        Time per character in the ASCII graph. Default 1 day.
    log_level : str or int, optional
        Log level for the ASCII graph. Default "INFO".
    """

    def __init__(self, inputs, time_step=timedelta(days=1), log_level="INFO"):
        super().__init__()
        self._pull_inputs = inputs
        self._time_step = time_step
        self._log_level = logging.getLevelName(log_level)

        self._schedule = None
        self._output_map = None

    def _initialize(self):
        for inp in self._pull_inputs:
            self.inputs.add(
                CallbackInput(self._data_changed, name=inp, time=None, grid=None)
            )
        self.create_connector(
            pull_data=[inp for inp, pull in self._pull_inputs.items() if pull]
        )

    def _connect(self):
        self.try_connect()

    def _validate(self):
        pass

    def _data_changed(self, caller, time):
        self._update_schedule(caller, time)

    def _update(self):
        pass

    def _update_schedule(self, caller, time):
        if self._schedule is None:
            self._schedule = {inp: [] for _, inp in self.inputs.items()}
            self._output_map = {}
            for _, inp in self.inputs.items():
                out = inp
                while isinstance(out, IInput):
                    out = out.get_source()
                self._output_map[inp] = out

        self._schedule[caller].append(time)

        if self._pull_inputs[caller.name]:
            _data = caller.pull_data(time)

        if self.status == ComponentStatus.VALIDATED:
            self._print_schedule(caller)

    def _print_schedule(self, caller):
        t_min = min(t[0] for _, t in self._schedule.items() if len(t) > 0)
        t_max = max(t[-1] for _, t in self._schedule.items() if len(t) > 0)
        t_diff = t_max - t_min

        num_char = int(t_diff / self._time_step) + 1

        self.logger.log(self._log_level, "input updated")

        max_name_len = max(len(inp.name) for inp in self._schedule)

        for inp, times in self._schedule.items():
            if len(times) == 0:
                continue

            s = [" "] * num_char

            out = self._output_map[inp]

            data_cache = getattr(out, "data", [])
            data_len = len(data_cache)
            i_min = len(times) - data_len

            prev = 0
            for i, t in enumerate(times):
                d = t - t_min
                pos = int(d / self._time_step)
                for j in range(prev, pos):
                    s[j] = "-"

                s[pos] = "o" if i >= i_min else "x"
                prev = pos + 1

            s = "".join(s)

            if inp == caller:
                s += " <-"

            self.logger.log(self._log_level, "%s %s", inp.name.ljust(max_name_len), s)
