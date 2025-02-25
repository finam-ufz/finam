"""
Modules for reading data.
"""
# pylint: disable=E1101
from datetime import datetime

from finam.interfaces import ComponentStatus

from ..data.grid_spec import NoGrid
from ..data.tools import Info, quantify
from ..sdk import TimeComponent


class CsvReader(TimeComponent):
    """Reads CSV time series with one row per time step, and emits values based on a time column.

    .. code-block:: text

        +-----------+
        |           | [custom] -->
        | CsvReader | [custom] -->
        |           | [......] -->
        +-----------+

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        reader = fm.components.CsvReader(
            path="test.csv",
            time_column="T",
            outputs={
                "A": "meter",
                "B": "",
            },
            date_format=None,
            separator=",",
        )

    .. testcode:: constructor
        :hide:

        reader.initialize()

    Parameters
    ----------
    path : PathLike
        Path to the input file.
    time_column
        Time column name.
    outputs : dict(str, str)
        Data column names and units. Names become output names.
        Use ``""`` for dimensionless columns and ``None`` to get units from connected components.
    date_format : optional
        Format specifier for date.
        See `datetime.strftime <https://docs.python.org/3/library/time.html#time.strftime>`_ for details.
        Default is ISO format.
    separator : str
        Columns separator. Default ";"
    """

    def __init__(self, path, time_column, outputs, date_format=None, separator=";"):
        super().__init__()
        self._path = path
        self._time = None
        self._time_column = time_column
        self._date_format = date_format
        self._separator = separator
        self._data = None
        self._row_index = 0
        self._data_generated = False

        self._output_units = outputs

    def _next_time(self):
        return None

    def _initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        for name in self._output_units:
            self.outputs.add(name=name)

        self.create_connector()

    def _connect(self, start_time):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        import pandas

        push_data = {}
        if not self._data_generated:
            self._data = pandas.read_csv(self._path, sep=self._separator)
            row = self._data.iloc[0]

            self._time, out_data = self._push_row(row, False)
            self._row_index = 1

            if all(
                info is not None for _name, info in self.connector.out_infos.items()
            ):
                push_data = out_data
                self._data_generated = True

        self.try_connect(
            start_time=start_time,
            push_infos={
                name: Info(self.time, grid=NoGrid(), units=units)
                for name, units in self._output_units.items()
            },
            push_data=push_data,
        )

    def _validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """

    def _update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        self._time, _ = self._push_row(self._data.iloc[self._row_index], True)
        self._row_index += 1

        if self._row_index >= self._data.shape[0]:
            self.status = ComponentStatus.FINISHED

    def _finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """

    def _push_row(self, row, push):
        if self._date_format is None:
            time = datetime.fromisoformat(row[self._time_column])
        else:
            time = datetime.strptime(row[self._time_column], self._date_format)

        out_data = {
            name: quantify(row[name], units)
            for name, units in self._output_units.items()
        }

        if push:
            for o in self._output_units:
                self.outputs[o].push_data(out_data[o], time)

        return time, out_data
