"""Generic component based on a callback."""

from datetime import datetime, timedelta

from ..sdk import TimeComponent
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

        component = fm.modules.CallbackComponent(
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
    start : datetime.datatime
        Start date and time
    step : timedelta
        Time step
    """

    def __init__(self, inputs, outputs, callback, start, step):
        super().__init__()

        with ErrorLogger(self.logger):
            if not isinstance(start, datetime):
                raise ValueError("Start must be of type datetime")
            if not isinstance(step, timedelta):
                raise ValueError("Step must be of type timedelta")

        self._input_infos = inputs
        self._output_infos = outputs
        self._callback = callback
        self._step = step
        self._time = start
        self._data_generated = False

    def _initialize(self):
        for name, info in self._input_infos.items():
            info.time = self.time
            self.inputs.add(name=name, info=info)

        for name, info in self._output_infos.items():
            info.time = self.time
            self.outputs.add(name=name, info=info)

        self.create_connector(pull_data=list(self._input_infos))

    def _connect(self):
        push_data = {}
        if not self._data_generated:
            if self.connector.all_data_pulled:
                push_data = self._callback(self.connector.in_data, self.time)
                self._data_generated = True

        self.try_connect(self._time, push_data=push_data)

    def _validate(self):
        pass

    def _update(self):
        inp = {n: self.inputs[n].pull_data(self.time) for n in self._input_infos.keys()}

        self._time += self._step

        outp = self._callback(inp, self.time)
        for name, val in outp.items():
            self.outputs[name].push_data(val, self.time)

    def _finalize(self):
        pass
