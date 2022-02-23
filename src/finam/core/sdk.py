"""
Implementations of the coupling interfaces for simpler development of modules and adapters.
"""

from abc import ABC
from datetime import datetime, timedelta

from .interfaces import (
    IInput,
    IOutput,
    IAdapter,
    IComponent,
    ITimeComponent,
    ComponentStatus,
)


class FinamStatusError(Exception):
    """Error for wrong status in Component."""


class AComponent(IComponent, ABC):
    """
    Abstract component implementation.
    """

    def __init__(self):
        self._status = None
        self._inputs = {}
        self._outputs = {}

    def initialize(self):
        if self._status != ComponentStatus.CREATED:
            raise FinamStatusError(
                f"Unexpected model state {self._status} in {self.name}"
            )

    def connect(self):
        if self._status != ComponentStatus.INITIALIZED:
            raise FinamStatusError(
                f"Unexpected model state {self._status} in {self.name}"
            )

    def validate(self):
        if self._status != ComponentStatus.CONNECTED:
            raise FinamStatusError(
                f"Unexpected model state {self._status} in {self.name}"
            )

    def update(self):
        if not (
            self._status == ComponentStatus.VALIDATED
            or self._status == ComponentStatus.UPDATED
        ):
            raise FinamStatusError(
                f"Unexpected model state {self._status} in {self.name}"
            )

    def finalize(self):
        if not (
            self._status == ComponentStatus.UPDATED
            or self._status == ComponentStatus.FINISHED
        ):
            raise FinamStatusError(
                f"Unexpected model state {self._status} in {self.name}"
            )

    def inputs(self):
        return self._inputs

    def outputs(self):
        return self._outputs

    def status(self):
        return self._status


class ATimeComponent(ITimeComponent, AComponent, ABC):
    """
    Abstract component with time step implementation.
    """

    def __init__(self):
        super(ATimeComponent, self).__init__()
        self._time = None

    def time(self):
        if not isinstance(self._time, datetime):
            raise ValueError("Time must be of type datetime")

        return self._time


class Input(IInput):
    """
    Default input implementation.
    """

    def __init__(self):
        self.source = None

    def set_source(self, source):
        if self.source is not None:
            raise ValueError(
                "Source of input is already set! "
                "(You probably tried to connect multiple outputs to a single input)"
            )

        if not isinstance(source, IOutput):
            raise ValueError("Only IOutput can be set as source for Input")

        self.source = source

    def get_source(self):
        return self.source

    def source_changed(self, time):
        pass

    def pull_data(self, time):
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        return self.source.get_data(time)


class CallbackInput(Input, IInput):
    """
    Input implementation calling a callback when notified.

    Use for components without time step.
    """

    def __init__(self, callback):
        self.source = None
        self.callback = callback

    def source_changed(self, time):
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        self.callback(self, time)


class Output(IOutput):
    """
    Default output implementation.
    """

    def __init__(self):
        self.targets = []
        self.data = []

    def add_target(self, target):
        if not isinstance(target, IInput):
            raise ValueError("Only IInput can added as target for IOutput")

        self.targets.append(target)

    def get_targets(self):
        return self.targets

    def push_data(self, data, time):
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        self.data = data
        self.notify_targets(time)

    def notify_targets(self, time):
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        for target in self.targets:
            target.source_changed(time)

    def get_data(self, time):
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        return self.data

    def chain(self, other):
        self.add_target(other)
        other.set_source(self)
        return other


class AAdapter(IAdapter, Input, Output, ABC):
    """
    Abstract adapter implementation.
    """

    def __init__(self):
        super().__init__()
        self.source = None
        self.targets = []

    def push_data(self, data, time):
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        self.notify_targets(time)

    def source_changed(self, time):
        if not isinstance(time, datetime):
            raise ValueError("Time must be of type datetime")

        self.notify_targets(time)
