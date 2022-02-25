"""Generic component based on a callback."""

from datetime import datetime, timedelta

from ..core.interfaces import ComponentStatus
from ..core.sdk import ATimeComponent, Input, Output


class CallbackComponent(ATimeComponent):
    """Component to generate, transform or consume data in fixed time intervals using a callback.

    Parameters
    ----------
    inputs : list of str
        Input names.
    outputs : list of str
        Output names.
    callback
        Callback f({inputs}, time) -> {outputs}
    start : datetime
        Start date and time
    step : timedelta
        Time step
    """

    def __init__(self, inputs, outputs, callback, start, step):
        super().__init__()

        if not isinstance(start, datetime):
            raise ValueError("Start must be of type datetime")
        if not isinstance(step, timedelta):
            raise ValueError("Step must be of type timedelta")

        self._input_names = inputs
        self._output_names = outputs
        self._callback = callback
        self._step = step
        self._time = start
        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        for name in self._input_names:
            self._inputs[name] = Input()

        for name in self._output_names:
            self._outputs[name] = Output()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        inp = {n: None for n in self._input_names}
        outp = self._callback(inp, self.time)

        for name, val in outp.items():
            self._outputs[name].push_data(val, self.time)

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        inp = {n: self.inputs[n].pull_data(self.time) for n in self._input_names}

        self._time += self._step

        outp = self._callback(inp, self.time)
        for name, val in outp.items():
            self._outputs[name].push_data(val, self.time)

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED
