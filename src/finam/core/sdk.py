"""
Implementations of the coupling interfaces for simpler development of modules and adapters.
"""

from abc import ABC
from .interfaces import (
    IInput,
    IOutput,
    IAdapter,
    IComponent,
    ITimeComponent,
    ComponentStatus,
)


class AComponent(IComponent, ABC):
    """
    Abstract component implementation.
    """

    def __init__(self):
        self._status = None
        self._inputs = {}
        self._outputs = {}

    def initialize(self):
        assert (
            self._status == ComponentStatus.CREATED
        ), f"Unexpected model state {self._status} in {self.__class__.__name__}"

    def connect(self):
        assert (
            self._status == ComponentStatus.INITIALIZED
        ), f"Unexpected model state {self._status} in {self.__class__.__name__}"

    def validate(self):
        assert (
            self._status == ComponentStatus.CONNECTED
        ), f"Unexpected model state {self._status} in {self.__class__.__name__}"

    def update(self):
        assert (
            self._status == ComponentStatus.VALIDATED
            or self._status == ComponentStatus.UPDATED
        ), f"Unexpected model state {self._status} in {self.__class__.__name__}"

    def finalize(self):
        assert (
            self._status == ComponentStatus.UPDATED
            or self._status == ComponentStatus.FINISHED
        ), f"Unexpected model state {self._status} in {self.__class__.__name__}"

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
        self._time = 0

    def time(self):
        return self._time


class Input(IInput):
    """
    Default input implementation.
    """

    def __init__(self):
        self.source = None

    def set_source(self, source):
        assert (
            self.source is None
        ), "Source of input is already set! (You probably tried to connect multiple outputs to a single input)"
        self.source = source

    def get_source(self):
        return self.source

    def source_changed(self, time):
        pass

    def pull_data(self, time):
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
        self.callback(self, time)


class Output(IOutput):
    """
    Default output implementation.
    """

    def __init__(self):
        self.targets = []
        self.data = []

    def add_target(self, target):
        self.targets.append(target)

    def get_targets(self):
        return self.targets

    def push_data(self, data, time):
        self.data = data
        self.notify_targets(time)

    def notify_targets(self, time):
        for target in self.targets:
            target.source_changed(time)

    def get_data(self, time):
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
        self.notify_targets(time)

    def source_changed(self, time):
        self.notify_targets(time)
