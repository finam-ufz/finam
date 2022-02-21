from datetime import datetime

from ...core.sdk import AComponent, ATimeComponent, Input, CallbackInput
from ...core.interfaces import ComponentStatus


class ScheduleView(AComponent):
    """
    Live visualization of module update schedule.

    Takes inputs of arbitrary types and simply plots the time of notifications of each input.

    .. code-block:: text

                     +--------------+
        --> [custom] |              |
        --> [custom] | ScheduleView |
        --> [......] |              |
                     +--------------+

    :param inputs: List of input names that will become available for coupling
    """

    def __init__(self, inputs):
        """
        Create a schedule viewer
        """
        super(ScheduleView, self).__init__()
        self._time = None
        self._caller = None
        self._figure = None
        self._axes = None
        self._lines = None
        self._x = [[] for _ in inputs]

        self._input_names = inputs
        self._inputs = {inp: CallbackInput(self.data_changed) for inp in inputs}

        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()

        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        self._figure, self._axes = plt.subplots(figsize=(8, 3))

        date_format = mdates.AutoDateFormatter(self._axes.xaxis)
        self._axes.xaxis.set_major_formatter(date_format)
        self._axes.tick_params(axis="x", labelrotation=20)
        self._axes.set_yticks(range(len(self._input_names)))
        self._axes.set_yticklabels(self._input_names)

        self._figure.tight_layout()
        self._figure.show()

        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()

        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()
        self.update_plot()
        self._status = ComponentStatus.VALIDATED

    def data_changed(self, caller, time):
        self._caller = caller
        self._time = time

        if (
            self._status == ComponentStatus.UPDATED
            or self._status == ComponentStatus.VALIDATED
        ):
            self.update()
        else:
            self.update_plot()

    def update(self):
        super().update()

        self.update_plot()

        self._status = ComponentStatus.UPDATED

    def update_plot(self):
        if self._lines is None:
            self._lines = [
                self._axes.plot([datetime.min], i, marker="+", label=h)[0]
                for i, h in enumerate(self._input_names)
            ]

        for i, inp in enumerate(self._input_names):
            if self._inputs[inp] == self._caller:
                self._x[i].append(self._time)

        for i, line in enumerate(self._lines):
            line.set_xdata(self._x[i])
            line.set_ydata(i)

        self._axes.relim()
        self._axes.autoscale_view(True, True, True)

        self._figure.canvas.draw()
        self._figure.canvas.flush_events()

    def finalize(self):
        super().finalize()

        self._status = ComponentStatus.FINALIZED
