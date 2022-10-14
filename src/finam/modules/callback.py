"""Generic component based on a callback."""

from datetime import datetime, timedelta

from ..core.interfaces import ComponentStatus
from ..core.sdk import ATimeComponent
from ..tools.connect_helper import ConnectHelper
from ..tools.log_helper import LogError


class CallbackComponent(ATimeComponent):
    """Component to generate, transform or consume data in fixed time intervals using a callback.

    Parameters
    ----------
    inputs : dict of (name, info)
        Input names and data info.
    outputs : dict of (name, info)
        Output names and data info.
    callback
        Callback f({inputs}, time) -> {outputs}
    start : datetime
        Start date and time
    step : timedelta
        Time step
    """

    def __init__(self, inputs, outputs, callback, start, step):
        super().__init__()

        with LogError(self.logger):
            if not isinstance(start, datetime):
                raise ValueError("Start must be of type datetime")
            if not isinstance(step, timedelta):
                raise ValueError("Step must be of type timedelta")

        self._input_infos = inputs
        self._output_infos = outputs
        self._callback = callback
        self._step = step
        self._time = start
        self._connector = None
        self.status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        for name, info in self._input_infos.items():
            self.inputs.add(name=name, info=info)

        for name, info in self._output_infos.items():
            self.outputs.add(name=name, info=info)

        self._connector = ConnectHelper(self.inputs, self.outputs)

        self.status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        inp = {n: None for n in self._input_infos.keys()}
        outp = self._callback(inp, self.time)

        self.status = self._connector.connect(self._time, push_data=outp)

    def validate(self):
        super().validate()

        self.status = ComponentStatus.VALIDATED

    def update(self):
        super().update()

        inp = {n: self.inputs[n].pull_data(self.time) for n in self._input_infos.keys()}

        self._time += self._step

        outp = self._callback(inp, self.time)
        for name, val in outp.items():
            self.outputs[name].push_data(val, self.time)

        self.status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()

        self.status = ComponentStatus.FINALIZED
