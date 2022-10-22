"""Generic component based on a callback."""

from datetime import datetime, timedelta

from ..sdk import TimeComponent
from ..tools.log_helper import ErrorLogger

__all__ = ["CallbackComponent"]


class CallbackComponent(TimeComponent):
    """Component to generate, transform or consume data in fixed time intervals using a callback.

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

    def _initialize(self):
        for name, info in self._input_infos.items():
            info.time = self.time
            self.inputs.add(name=name, info=info)

        for name, info in self._output_infos.items():
            info.time = self.time
            self.outputs.add(name=name, info=info)

        self.create_connector()

    def _connect(self):
        inp = {n: None for n in self._input_infos.keys()}
        outp = self._callback(inp, self.time)

        self.try_connect(self._time, push_data=outp)

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
