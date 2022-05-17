"""Grid visualizations."""
# pylint: disable=W0613
from datetime import datetime, timedelta

from ...core.interfaces import ComponentStatus
from ...core.sdk import AComponent, ATimeComponent, CallbackInput, Input
from ...data import assert_type
from ...data.grid import Grid


class GridView(AComponent):
    """Live grid viewer module, updating on pushed input changes.

    .. code-block:: text

                 +----------+
        --> Grid | GridView |
                 +----------+
    """

    def __init__(self, vmin=None, vmax=None):
        super().__init__()
        self._time = None
        self._image = None
        self._figure = None
        self._text = None

        self.vmin = vmin
        self.vmax = vmax

        self._status = ComponentStatus.CREATED

    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        super().initialize()

        self._inputs["Grid"] = CallbackInput(self.data_changed)

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

    def data_changed(self, caller, time):
        """Update for changed data.

        Parameters
        ----------
        caller
            Caller.
        time : datetime
            simulation time to get the data for.
        """
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

        self._time = time
        if self._status in (ComponentStatus.UPDATED, ComponentStatus.VALIDATED):
            self.update()
        else:
            self.update_plot()

    def update(self):
        """Update the component by one time step and push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        super().update()

        self.update_plot()

        self._status = ComponentStatus.UPDATED

    def update_plot(self):
        """Update the plot."""
        import matplotlib.pyplot as plt

        grid = self._inputs["Grid"].pull_data(self._time)
        try:
            assert_type(self, "Grid", grid, [Grid])
        except TypeError as err:
            self.logger.exception(err)
            raise

        img = grid.reshape(grid.spec.nrows, grid.spec.ncols)

        if self._image is None:
            self._figure, ax = plt.subplots()
            ax.axis("off")
            self._figure.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.06)
            self._figure.show()

            self._image = ax.imshow(
                img, interpolation=None, vmin=self.vmin, vmax=self.vmax
            )
            self._text = ax.text(5, 5, f"T: {self._time}", transform=None, fontsize=14)
        else:
            self._image.set_data(img)
            self._text.set_text(f"T: {self._time}")

        self._figure.canvas.draw()
        self._figure.canvas.flush_events()

    def finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
        super().finalize()

        self._status = ComponentStatus.FINALIZED


class TimedGridView(ATimeComponent, GridView):
    """Live grid viewer module, updating in regular intervals.

    .. code-block:: text

                 +---------------+
        --> Grid | TimedGridView |
                 +---------------+
    """

    def __init__(self, start, step, vmin=None, vmax=None):
        ATimeComponent.__init__(self)
        GridView.__init__(self, vmin, vmax)
        try:
            if not isinstance(start, datetime):
                raise ValueError("Start must be of type datetime")
            if not isinstance(step, timedelta):
                raise ValueError("Step must be of type timedelta")
        except ValueError as err:
            self.logger.exception(err)
            raise

        self._time = start
        self._step = step

    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        super().initialize()

        self._inputs["Grid"] = Input()

    def update(self):
        """Update the component by one time step and push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        super().update()

        self._time += self._step
