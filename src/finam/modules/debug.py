"""Generic component with arbitrary inputs and extensive debug logging."""

from datetime import datetime, timedelta

from ..core.interfaces import ComponentStatus
from ..core.sdk import ATimeComponent
from ..tools.log_helper import LogError


class DebugConsumer(ATimeComponent):
    """Generic component with arbitrary inputs and extensive debug logging.

    Parameters
    ----------
    inputs : dict[str, Info]
    """

    def __init__(self, inputs, start, step):
        super().__init__()

        with LogError(self.logger):
            if not isinstance(start, datetime):
                raise ValueError("Start must be of type datetime")
            if not isinstance(step, timedelta):
                raise ValueError("Step must be of type timedelta")

        self._input_infos = inputs
        self._step = step
        self._time = start
        self.data = None
        self.status = ComponentStatus.CREATED

    def _initialize(self):
        for name, info in self._input_infos.items():
            self.inputs.add(name=name, info=info)
        self.create_connector(required_in_data=list(self._input_infos.keys()))

    def _connect(self):
        self.try_connect(self._time)
        for name, info in self.connector.in_infos.items():
            if info is not None:
                self.logger.debug("Exchanged input info for %s", name)
        for name, data in self.connector.in_data.items():
            if data is not None:
                self.logger.debug("Pulled input data for %s", name)

    def _validate(self):
        pass

    def _update(self):
        self.data = {
            n: self.inputs[n].pull_data(self.time) for n in self._input_infos.keys()
        }
        self._time += self._step

    def _finalize(self):
        pass
