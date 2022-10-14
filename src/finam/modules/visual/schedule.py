"""Schedule visualization."""

from datetime import datetime

from ...core.interfaces import ComponentStatus
from ...core.sdk import AComponent, CallbackInput
from ...data import Info, NoGrid


class ScheduleView(AComponent):
    """Live visualization of module update schedule.

    Takes inputs of arbitrary types and simply plots the time of notifications of each input.

    .. code-block:: text

                     +--------------+
        --> [custom] |              |
        --> [custom] | ScheduleView |
        --> [......] |              |
                     +--------------+

    Parameters
    ----------
    inputs : list of str
        Input names.
    """

    def __init__(self, inputs):
        super().__init__()
        self._time = None
        self._caller = None
        self._figure = None
        self._axes = None
        self._lines = None
        self._x = [[] for _ in inputs]

        self._input_names = inputs
        for inp in inputs:
            self.inputs.add(CallbackInput(self.data_changed, name=inp))

        self.status = ComponentStatus.CREATED

    def _initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt

        self._figure, self._axes = plt.subplots(figsize=(8, 3))

        date_format = mdates.AutoDateFormatter(self._axes.xaxis)
        self._axes.xaxis.set_major_formatter(date_format)
        self._axes.tick_params(axis="x", labelrotation=20)
        self._axes.set_yticks(range(len(self._input_names)))
        self._axes.set_yticklabels(self._input_names)

        self._figure.tight_layout()
        self._figure.show()

        self.create_connector()

    def _connect(self):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        self.try_connect(
            exchange_infos={name: Info(grid=NoGrid()) for name in self.inputs}
        )

    def _validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """
        self.update_plot()

    def data_changed(self, caller, time):
        """Update for changed data.

        Parameters
        ----------
        caller
            Caller.
        time : datetime
            simulation time to get the data for.
        """
        self._caller = caller
        self._time = time

        if self.status in (ComponentStatus.UPDATED, ComponentStatus.VALIDATED):
            self.update()
        else:
            self.update_plot()

    def _update(self):
        """Update the component by one time step and push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        self.update_plot()

    def update_plot(self):
        """Update the plot."""
        if self._lines is None:
            self._lines = [
                self._axes.plot([datetime.min], i, marker="+", label=h)[0]
                for i, h in enumerate(self._input_names)
            ]

        for i, inp in enumerate(self._input_names):
            if self.inputs[inp] == self._caller:
                self._x[i].append(self._time)

        for i, line in enumerate(self._lines):
            line.set_xdata(self._x[i])
            line.set_ydata(i)

        self._axes.relim()
        self._axes.autoscale_view(True, True, True)

        self._figure.canvas.draw()
        self._figure.canvas.flush_events()

    def _finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
