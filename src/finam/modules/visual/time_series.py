"""Time series visualization."""

from datetime import datetime, timedelta

from ...core.interfaces import ComponentStatus
from ...core.sdk import ATimeComponent, Input
from ...data import assert_type


class TimeSeriesView(ATimeComponent):
    """Live time series viewer.

    Expects all inputs to be scalar values.

    .. code-block:: text

                     +----------------+
        --> [custom] |                |
        --> [custom] | TimeSeriesView |
        --> [......] |                |
                     +----------------+

    Parameters
    ----------
    inputs : list of str
        List of input names (plot series) that will become available for coupling.
    start : datetime
        Starting time.
    step : timedelta
        Time step.
    intervals : list of int or None, optional
        List of interval values to interleave data retrieval of certain inputs.
        Values are numbers of updates, i.e. whole-numbered factors for ``step``.
    update_interval : int, optional
         Redraw interval (independent of data retrieval).
    """

    def __init__(self, inputs, start, step, intervals=None, update_interval=1):
        super().__init__()
        try:
            if not isinstance(start, datetime):
                raise ValueError("Start must be of type datetime")
            if not isinstance(step, timedelta):
                raise ValueError("Step must be of type timedelta")
        except ValueError as err:
            self.logger.exception(err)
            raise

        self._step = step
        self._update_interval = update_interval
        self._intervals = intervals if intervals else [1 for _ in inputs]
        self._time = start
        self._updates = 0
        self._figure = None
        self._axes = None
        self._data = [[] for _ in inputs]
        self._x = [[] for _ in inputs]
        self._lines = None

        self._input_names = inputs
        self._inputs = {inp: Input() for inp in inputs}

        self._status = ComponentStatus.CREATED

    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        super().initialize()

        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt

        self._figure, self._axes = plt.subplots()
        date_format = mdates.AutoDateFormatter(self._axes.xaxis)
        self._axes.xaxis.set_major_formatter(date_format)
        self._axes.tick_params(axis="x", labelrotation=20)

        self._figure.show()

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

        if self._lines is None:
            self._lines = [
                self._axes.plot([], [], label=h)[0] for h in self._input_names
            ]
            self._axes.legend(loc=1)

        for i, inp in enumerate(self._input_names):
            if self._updates % self._intervals[i] == 0:
                value = self._inputs[inp].pull_data(self.time)
                try:
                    assert_type(self, inp, value, [int, float])
                except TypeError as err:
                    self.logger.exception(err)
                    raise

                self._x[i].append(self.time)
                self._data[i].append(value)

        if self._updates % self._update_interval == 0:
            for i, line in enumerate(self._lines):
                line.set_xdata(self._x[i])
                line.set_ydata(self._data[i])

            self._axes.relim()
            self._axes.autoscale_view(True, True, True)

            self._figure.canvas.draw()
            self._figure.canvas.flush_events()

        self._time += self._step
        self._updates += 1

        self._status = ComponentStatus.UPDATED

    def finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
        super().finalize()

        self._status = ComponentStatus.FINALIZED
