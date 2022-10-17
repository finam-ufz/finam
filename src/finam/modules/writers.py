"""
Modules for writing data.
"""
from datetime import datetime, timedelta

import numpy as np

from .. import ATimeComponent, ComponentStatus, NoGrid
from .. import data as fmdata
from ..tools import LogError


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
        with LogError(self.logger):
            if not isinstance(start, datetime):
                raise ValueError("Start must be of type datetime")
            if not isinstance(step, timedelta):
                raise ValueError("Step must be of type timedelta")

        self._path = path
        self._step = step
        self._time = start

        self._input_names = inputs

        self._rows = []

        self.status = ComponentStatus.CREATED

    def _initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        for inp in self._input_names:
            self.inputs.add(name=inp, grid=NoGrid(), units=None)

        self.create_connector()

    def _connect(self):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        self.try_connect()

    def _validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """

    def _update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        values = [
            fmdata.get_magnitude(
                fmdata.strip_time(self.inputs[inp].pull_data(self.time))
            )
            for inp in self._input_names
        ]
        with LogError(self.logger):
            for (value, name) in zip(values, self._input_names):
                fmdata.assert_type(self, name, value.item(), [int, float])

        self._rows.append([self.time.isoformat()] + values)

        self._time += self._step

    def _finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
        np.savetxt(
            self._path,
            self._rows,
            fmt="%s",
            delimiter=";",
            header=";".join(["time"] + self._input_names),
            comments="",
        )
