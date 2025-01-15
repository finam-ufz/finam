"""
Modules for writing data.
"""
from datetime import datetime

import numpy as np

from ..data import tools as dtools
from ..data.grid_spec import NoGrid
from ..interfaces import ComponentStatus
from ..sdk import TimeComponent
from ..tools.date_helper import is_timedelta
from ..tools.log_helper import ErrorLogger


class CsvWriter(TimeComponent):
    """Writes CSV time series with one row per time step, from multiple inputs.

    Expects all inputs to be scalar values.

    .. code-block:: text

                     +-----------+
        --> [custom] |           |
        --> [custom] | CsvWriter |
        --> [......] |           |
                     +-----------+

    Examples
    --------

    .. testcode:: constructor

        import datetime as dt
        import finam as fm

        writer = fm.components.CsvWriter(
            path="test.csv",
            inputs=["A", "B", "C"],
            time_column="T",
            separator=",",
            start=dt.datetime(2000, 1, 1),
            step=dt.timedelta(days=1),
        )

    .. testcode:: constructor
        :hide:

        writer.initialize()

    Parameters
    ----------
    path : PathLike
        Path to the output file.
    inputs : list of str
        List of input names that will be written to file.
    start : :class:`datetime <datetime.datetime>`
        Starting time.
    step : :class:`timedelta <datetime.timedelta>` or :class:`relativedelta <dateutil.relativedelta.relativedelta>`
        Time step.
    time_column : str
        Time column name. Default "time"
    separator : str
        Column separator. Default ";"
    """

    def __init__(self, path, start, step, inputs, time_column="time", separator=";"):
        super().__init__()
        with ErrorLogger(self.logger):
            if not isinstance(start, datetime):
                raise ValueError("Start must be of type datetime")
            if not is_timedelta(step):
                raise ValueError("Step must be of type timedelta or relativedelta")

        self._path = path
        self._step = step
        self._time = start
        self._time_column = time_column
        self._separator = separator

        self._input_names = inputs

        self._rows = []

    def _next_time(self):
        return self.time + self._step

    def _initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        for inp in self._input_names:
            self.inputs.add(name=inp, time=None, grid=NoGrid(), units=None)

        self.create_connector(pull_data=self._input_names)

    def _connect(self, start_time):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        self.try_connect(start_time)

        if self.status == ComponentStatus.CONNECTED:
            values = [
                dtools.get_magnitude(dtools.strip_time(data, NoGrid()))
                for _, data in self.connector.in_data.items()
            ]

            self._update_rows(values)

    def _validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """

    def _update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        self._time += self._step

        values = [
            dtools.get_magnitude(
                dtools.strip_time(self.inputs[inp].pull_data(self.time), NoGrid())
            )
            for inp in self._input_names
        ]
        self._update_rows(values)

    def _update_rows(self, values):
        with ErrorLogger(self.logger):
            for value, name in zip(values, self._input_names):
                dtools.assert_type(self, name, value.item(), [int, float])

        self._rows.append([self.time.isoformat()] + values)

    def _finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
        np.savetxt(
            self._path,
            self._rows,
            fmt="%s",
            delimiter=self._separator,
            header=self._separator.join([self._time_column] + self._input_names),
            comments="",
        )
