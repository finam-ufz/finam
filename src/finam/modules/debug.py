"""Generic component with arbitrary inputs and extensive debug logging."""

from datetime import datetime, timedelta

from ..sdk import TimeComponent
from ..tools.log_helper import ErrorLogger


class DebugConsumer(TimeComponent):
    """Generic component with arbitrary inputs and extensive debug logging.

    Parameters
    ----------
    inputs : dict[str, Info]
    """

    def __init__(self, inputs, start, step):
        super().__init__()

        with ErrorLogger(self.logger):
            if not isinstance(start, datetime):
                raise ValueError("Start must be of type datetime")
            if not isinstance(step, timedelta):
                raise ValueError("Step must be of type timedelta")

        self._input_infos = inputs
        self._step = step
        self._time = start
        self.data = {}

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
                self.data[name] = data

    def _validate(self):
        pass

    def _update(self):
        self.data = {
            n: self.inputs[n].pull_data(self.time) for n in self._input_infos.keys()
        }
        self._time += self._step

    def _finalize(self):
        pass
