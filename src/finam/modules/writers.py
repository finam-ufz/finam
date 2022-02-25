"""
Modules for writing data.
"""
from datetime import datetime, timedelta

import numpy as np

from ..core.interfaces import ComponentStatus
from ..core.sdk import ATimeComponent, Input
from ..data import assert_type


class CsvWriter(ATimeComponent):
    """Writes CSV time series with one row per time step, from multiple inputs.

    Expects all inputs to be scalar values.

    .. code-block:: text

                     +-----------+
        --> [custom] |           |
        --> [custom] | CsvWriter |
        --> [......] |           |
                     +-----------+

    Parameters
    ----------
    path : PathLike
        Path to the output file.
    start : datetime
        Starting time.
    step : timedelta
        Time step.
    inputs : list of str
        List of input names that will be written to file.
    """

    def __init__(self, path, start, step, inputs):
        super().__init__()

        if not isinstance(start, datetime):
            raise ValueError("Start must be of type datetime")
        if not isinstance(step, timedelta):
            raise ValueError("Step must be of type timedelta")

        self._path = path
        self._step = step
        self._time = start

        self._input_names = inputs
        self._inputs = {inp: Input() for inp in inputs}

        self._rows = []

        self._status = ComponentStatus.CREATED

    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        super().initialize()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        super().connect()

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """
        super().validate()

        self._status = ComponentStatus.VALIDATED

    def update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        super().update()

        values = [self._inputs[inp].pull_data(self.time) for inp in self._input_names]

        for (value, name) in zip(values, self._input_names):
            assert_type(self, name, value, [int, float])

        self._rows.append([self.time.isoformat()] + values)

        self._time += self._step

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
        super().finalize()

        np.savetxt(
            self._path,
            self._rows,
            fmt="%s",
            delimiter=";",
            header=";".join(["time"] + self._input_names),
            comments="",
        )

        self._status = ComponentStatus.FINALIZED
