"""
Implementations of the coupling interfaces for simpler development of modules and adapters.
"""

from abc import ABC
from datetime import datetime

from .interfaces import (
    ComponentStatus,
    IAdapter,
    IComponent,
    IInput,
    IOutput,
    ITimeComponent,
)


class FinamStatusError(Exception):
    """Error for wrong status in Component."""


class AComponent(IComponent, ABC):
    """Abstract component implementation."""

    def __init__(self):
        self._status = None
        self._inputs = {}
        self._outputs = {}

    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        if self._status != ComponentStatus.CREATED:
            raise FinamStatusError(
                f"Unexpected model state {self._status} in {self.name}"
            )

    def connect(self):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        if self._status != ComponentStatus.INITIALIZED:
            raise FinamStatusError(
                f"Unexpected model state {self._status} in {self.name}"
            )

    def validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """
        if self._status != ComponentStatus.CONNECTED:
            raise FinamStatusError(
                f"Unexpected model state {self._status} in {self.name}"
            )

    def update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        if not self._status in (ComponentStatus.VALIDATED, ComponentStatus.UPDATED):
            raise FinamStatusError(
                f"Unexpected model state {self._status} in {self.name}"
            )

    def finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
        if not self._status in (ComponentStatus.UPDATED, ComponentStatus.FINISHED):
            raise FinamStatusError(
                f"Unexpected model state {self._status} in {self.name}"
            )

    @property
    def inputs(self):
        """dict: The component's inputs."""
        return self._inputs

    @property
    def outputs(self):
        """dict: The component's outputs."""
        return self._outputs

    @property
    def status(self):
        """The component's current status."""
        return self._status


class ATimeComponent(ITimeComponent, AComponent, ABC):
    """Abstract component with time step implementation."""

    def __init__(self):
        super().__init__()
        self._time = None

    @property
    def time(self):
        """The component's current simulation time."""
        if not isinstance(self._time, datetime):
            raise ValueError("Time must be of type datetime")

        return self._time


class Input(IInput):
    """Default input implementation."""

    def __init__(self):
        self.source = None

    def set_source(self, source):
        """Set the input's source output or adapter

        Parameters
        ----------
        source :
            source output or adapter
        """
        if self.source is not None:
            raise ValueError(
                "Source of input is already set! "
                "(You probably tried to connect multiple outputs to a single input)"
            )

        if not isinstance(source, IOutput):
            raise ValueError("Only IOutput can be set as source for Input")

        self.source = source

    def get_source(self):
        """Get the input's source output or adapter

        Returns
        -------
        Output
            The input's source.
        """
        return self.source

    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """

    def pull_data(self, time):
        """Retrieve the data from the input's source.

        Parameters
        ----------
        time : datetime
            Simulation time to get the data for.

        Returns
        -------
        array_like
            Data set for the given simulation time.
        """
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        return self.source.get_data(time)

    @property
    def has_source(self):
        """Flag if this input instance has a source."""
        return self.source is not None


class CallbackInput(Input):
    """Input implementation calling a callback when notified.

    Use for components without time step.

    Parameters
    ----------
    callback : callable
        A callback ``callback(data, time)``, returning the transformed data.
    """

    def __init__(self, callback):
        super().__init__()
        self.source = None
        self.callback = callback

    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        self.callback(self, time)


class Output(IOutput):
    """Default output implementation."""

    def __init__(self):
        self.targets = []
        self.data = []

    def add_target(self, target):
        """Add a target input or adapter for this output.

        Parameters
        ----------
        target : Input
            The target to add.
        """
        if not isinstance(target, IInput):
            raise ValueError("Only IInput can added as target for IOutput")

        self.targets.append(target)

    def get_targets(self):
        """Get target inputs and adapters for this output.

        Returns
        -------
        list
            List of targets.
        """
        return self.targets

    def push_data(self, data, time):
        """Push data into the output.

        Should notify targets, and can handle the provided date.

        Parameters
        ----------
        data : array_like
            Data set to push.
        time : datetime
            Simulation time of the data set.
        """
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        self.data = data
        self.notify_targets(time)

    def notify_targets(self, time):
        """Notify all targets by calling their ``source_changed(time)`` method.

        Parameters
        ----------
        time : datetime
            Simulation time of the simulation.
        """
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        for target in self.targets:
            target.source_changed(time)

    def get_data(self, time):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : datetime
            simulation time to get the data for.

        Returns
        -------
        array_like
            data-set for the requested time.
        """
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        return self.data

    def chain(self, other):
        """Chain outputs and adapters.

        Parameters
        ----------
        other : Output
            The adapter or output to add as target to this output.

        Returns
        -------
        Output
            The last element of the chain.
        """
        self.add_target(other)
        other.set_source(self)
        return other


class AAdapter(IAdapter, Input, Output, ABC):
    """Abstract adapter implementation."""

    def __init__(self):
        super().__init__()
        self.source = None
        self.targets = []

    def push_data(self, data, time):
        """Push data into the output.

        Should notify targets, and can handle the provided date.

        Parameters
        ----------
        data : array_like
            Data set to push.
        time : datetime
            Simulation time of the data set.
        """
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        self.notify_targets(time)

    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        self.notify_targets(time)
