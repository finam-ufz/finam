"""Generic component with arbitrary inputs and extensive debug logging."""
import logging
from datetime import datetime, timedelta

from ..data import tools
from ..interfaces import ComponentStatus, IInput
from ..sdk import CallbackInput, Component, TimeComponent
from ..tools.date_helper import is_timedelta


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

        component = fm.components.DebugConsumer(
            inputs={
                "A": fm.Info(time=None, grid=fm.NoGrid()),
                "B": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callbacks={
                "A": lambda n, d, t: print(t)
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
        Dictionary of input names and infos.
    callbacks : dict[str, callable]
        Dictionary of optional input callbacks: callable(name, data, time).
    start : :class:`datetime <datetime.datetime>`
        Starting time
    step : :class:`timedelta <datetime.timedelta>` or :class:`relativedelta <dateutil.relativedelta.relativedelta>`
        Time step
    log_data : int or str or bool, optional
        Log level for printing received data, like "DEBUG" or "INFO".
        Default ``False``, logs nothing.

        ``True`` uses "INFO".
    strip_data : bool, optional
        Strips data before logging. Default ``True``.
    """

    def __init__(
        self, inputs, start, step, callbacks=None, log_data=False, strip_data=True
    ):
        super().__init__()

        if not isinstance(start, datetime):
            raise ValueError("Start must be of type datetime")
        if not is_timedelta(step):
            raise ValueError("Step must be of type timedelta or relativedelta")

        self._strip_data = strip_data
        self._log_data = None
        if isinstance(log_data, bool):
            if log_data:
                self._log_data = logging.INFO
        else:
            self._log_data = logging.getLevelName(log_data)

        self._input_infos = inputs
        self._callbacks = callbacks or {}
        self._step = step
        self._time = start
        self._data = {}

    @property
    def data(self):
        """dict[str, data] : The component's input data from the last time step"""
        return self._data

    def _next_time(self):
        return self.time + self._step

    def _initialize(self):
        for name, info in self._input_infos.items():
            info.time = self.time
            self.inputs.add(name=name, info=info)
        self.create_connector(pull_data=list(self._input_infos.keys()))

    def _connect(self, start_time):
        self.try_connect(start_time)
        for name, info in self.connector.in_infos.items():
            if info is not None:
                self.logger.debug("Exchanged input info for %s", name)
        for name, data in self.connector.in_data.items():
            if data is not None:
                self.logger.debug("Pulled input data for %s", name)

                if self._log_data is not None:
                    pdata = (
                        tools.strip_time(data, self.inputs[name].info.grid)
                        if self._strip_data
                        else data
                    )
                    self.logger.log(
                        self._log_data,
                        'Received "%s" - %s: %s',
                        name,
                        self._time,
                        pdata,
                    )
                if name in self._callbacks:
                    self._callbacks[name](name, data, self._time)

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
                pdata = (
                    tools.strip_time(data, self.inputs[name].info.grid)
                    if self._strip_data
                    else data
                )
                self.logger.log(
                    self._log_data,
                    'Received "%s" - %s: %s',
                    name,
                    self._time,
                    pdata,
                )
            if name in self._callbacks:
                self._callbacks[name](name, data, self._time)

    def _finalize(self):
        pass


class DebugPushConsumer(Component):
    """Generic component with arbitrary inputs and extensive debug logging. Push-based.

    .. code-block:: text

                   +-------------------+
      --> [custom] |                   |
      --> [custom] | DebugPushConsumer |
      --> [......] |                   |
                   +-------------------+

    Examples
    --------

    .. testcode:: constructor

        import datetime as dt
        import finam as fm

        component = fm.components.DebugPushConsumer(
            inputs={
                "A": fm.Info(time=None, grid=fm.NoGrid()),
                "B": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callbacks={
                "A": lambda n, d, t: print(t)
            },
            log_data="INFO",
            strip_data=False,
        )

    .. testcode:: constructor
        :hide:

        component.initialize()



    Parameters
    ----------
    inputs : dict[str, Info]
        Dictionary of input names and infos.
    callbacks : dict[str, callable]
        Dictionary of optional input callbacks: callable(name, data, time).
    log_data : int or str or bool, optional
        Log level for printing received data, like "DEBUG" or "INFO".
        Default ``False``, logs nothing.

        ``True`` uses "INFO".
    strip_data : bool, optional
        Strips data before logging. Default ``True``.
    """

    def __init__(self, inputs, callbacks=None, log_data=False, strip_data=True):
        super().__init__()
        self._strip_data = strip_data
        self._log_data = None
        if isinstance(log_data, bool):
            if log_data:
                self._log_data = logging.INFO
        else:
            self._log_data = logging.getLevelName(log_data)

        self._input_infos = inputs
        self._callbacks = callbacks or {}
        self._data = {}

    @property
    def data(self):
        """dict[str, data] : The component's input data from the last time step"""
        return self._data

    def _initialize(self):
        for name, info in self._input_infos.items():
            self.inputs.add(
                CallbackInput(callback=self._data_pushed, name=name, info=info)
            )
        self.create_connector()

    def _connect(self, start_time):
        self.try_connect(start_time)
        for name, info in self.connector.in_infos.items():
            if info is not None:
                self.logger.debug("Exchanged input info for %s", name)

    def _validate(self):
        pass

    def _update(self):
        pass

    def _finalize(self):
        pass

    def _data_pushed(self, caller, time):
        data = caller.pull_data(time)
        self._data[caller.name] = data
        if self._log_data is not None:
            pdata = (
                tools.strip_time(data, caller.info.grid) if self._strip_data else data
            )
            self.logger.log(
                self._log_data,
                'Received "%s" - %s: %s',
                caller.name,
                time,
                pdata,
            )
        if caller.name in self._callbacks:
            self._callbacks[caller.name](caller.name, data, time)


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

        schedule = fm.components.ScheduleLogger(
            inputs={"Grid1": True, "Grid2": True},
            time_step=timedelta(days=1),
            log_level="DEBUG",
            stdout=True,
        )

    .. testcode:: constructor
        :hide:

        schedule.initialize()

    .. |relativedelta| replace:: :class:`relativedelta <dateutil.relativedelta.relativedelta>`

    Parameters
    ----------
    inputs : dict of str, bool
        Input names and whether to pull data from them when notified.
        Pulling is useful for correct output behaviour when clearing the data cache.
    time_step : :class:`timedelta <datetime.timedelta>` or |relativedelta|, optional
        Time per character in the ASCII graph. Default 1 day.
    log_level : str or int, optional
        Log level for the ASCII graph. Default "INFO".
    stdout : bool
        Prints the ASCII graphs to stdout.
        Useful for piping to file and/or for documentation
    """

    def __init__(
        self, inputs, time_step=timedelta(days=1), log_level="INFO", stdout=False
    ):
        super().__init__()
        self._pull_inputs = inputs
        self._time_step = time_step
        self._log_level = logging.getLevelName(log_level)
        self._stdout = stdout

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

    def _connect(self, start_time):
        self.try_connect(start_time)

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
                    out = out.source
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
        if self._stdout:
            print("")

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

            s = f"{inp.name.ljust(max_name_len)} {s}"
            self.logger.log(self._log_level, s)
            if self._stdout:
                print(s)
