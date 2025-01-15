"""Generic component based on a callback."""

from datetime import datetime

from ..sdk import TimeComponent
from ..tools.date_helper import is_timedelta
from ..tools.log_helper import ErrorLogger

__all__ = ["CallbackComponent"]


class CallbackComponent(TimeComponent):
    """Component to generate, transform or consume data in fixed time intervals using a callback.

    .. code-block:: text

                   +-------------------+
      --> [custom] |                   | [custom] -->
      --> [custom] | CallbackComponent |
      --> [......] |                   | [......] -->
                   +-------------------+

    Examples
    --------

    .. testcode:: constructor

        import datetime as dt
        import finam as fm

        component = fm.components.CallbackComponent(
            inputs={
                "A": fm.Info(time=None, grid=fm.NoGrid()),
                "B": fm.Info(time=None, grid=fm.NoGrid()),
            },
            outputs={
                "Sum": fm.Info(time=None, grid=fm.NoGrid()),
                "Diff": fm.Info(time=None, grid=fm.NoGrid()),
            },
            callback=lambda inp, _t: {
                "Sum": inp["A"] + inp["B"],
                "Diff": inp["A"] - inp["B"],
            },
            start=dt.datetime(2000, 1, 1),
            step=dt.timedelta(days=7),
        )

    .. testcode:: constructor
        :hide:

        component.initialize()

    Parameters
    ----------
    inputs : dict[str, Info]
        Input names and data info.
    outputs : dict[name, Info]
        Output names and data info.
    callback
        Callback f({inputs}, time) -> {outputs}
    start : :class:`datetime <datetime.datetime>`
        Start date and time
    step : :class:`timedelta <datetime.timedelta>` or :class:`relativedelta <dateutil.relativedelta.relativedelta>`
        Time step
    initial_pull : bool, optional
        whether to pull initial data. The first call of the callback with have ``None`` for inputs of disabled.
        Default ``True``.
    """

    def __init__(self, inputs, outputs, callback, start, step, initial_pull=True):
        super().__init__()

        with ErrorLogger(self.logger):
            if not isinstance(start, datetime):
                raise ValueError("Start must be of type datetime")
            if not is_timedelta(step):
                raise ValueError("Step must be of type timedelta or relativedelta")

        self._input_infos = inputs
        self._output_infos = outputs
        self._callback = callback
        self._step = step
        self._time = start
        self._initial_pull = initial_pull
        self._data_generated = False

    def _next_time(self):
        return self.time + self._step

    def _initialize(self):
        for name, info in self._input_infos.items():
            info.time = self.time
            self.inputs.add(name=name, info=info)

        for name, info in self._output_infos.items():
            info.time = self.time
            self.outputs.add(name=name, info=info)

        pull_data = list(self._input_infos) if self._initial_pull else {}

        self.create_connector(pull_data=pull_data)

    def _connect(self, start_time):
        push_data = {}
        if not self._data_generated:
            if self._initial_pull:
                if self.connector.all_data_pulled:
                    push_data = self._callback(self.connector.in_data, self.time)
                    self._data_generated = True
            else:
                push_data = self._callback(None, self.time)
                self._data_generated = True

        self.try_connect(start_time, push_data=push_data)

    def _validate(self):
        pass

    def _update(self):
        self._time += self._step

        inp = {n: self.inputs[n].pull_data(self.time) for n in self._input_infos.keys()}
        outp = self._callback(inp, self.time)
        for name, val in outp.items():
            if val is not None:
                self.outputs[name].push_data(val, self.time)

    def _finalize(self):
        pass
