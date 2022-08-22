"""
Implementations of the coupling interfaces for simpler development of modules and adapters.
"""
import logging
from abc import ABC
from datetime import datetime

from ..tools.log_helper import loggable
from .interfaces import (
    ComponentStatus,
    FinamLogError,
    FinamStatusError,
    IAdapter,
    IComponent,
    IInput,
    IOutput,
    ITimeComponent,
    Loggable,
)


class AComponent(IComponent, Loggable, ABC):
    """Abstract component implementation."""

    def __init__(self):
        self._status = None
        self._inputs = {}
        self._outputs = {}
        self.base_logger_name = None

    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        self.logger.debug("init")

    def connect(self):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        self.logger.debug("connect")

    def validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """
        self.logger.debug("validate")

    def update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        self.logger.debug("update")
        if isinstance(self, ITimeComponent):
            self.logger.debug("current time: %s", self.time)

    def finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
        self.logger.debug("finalize")

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

    @status.setter
    def status(self, status):
        """The component's current status."""
        if isinstance(status, ComponentStatus):
            self._status = status
        elif isinstance(status, int) and status in [e.value for e in ComponentStatus]:
            self._status = ComponentStatus(status)
        elif isinstance(status, str) and status in [e.name for e in ComponentStatus]:
            self._status = ComponentStatus[status]
        else:
            try:
                raise FinamStatusError(f"Unknown model state {status} in {self.name}")
            except FinamStatusError as err:
                self.logger.exception(err)
                raise

    @property
    def name(self):
        """Component name."""
        return self.__class__.__name__

    @property
    def logger_name(self):
        """Logger name derived from base logger name and class name."""
        base_logger = logging.getLogger(self.base_logger_name)
        # logger hierarchy indicated by "." in name
        return ".".join(([base_logger.name, self.name]))

    @property
    def uses_base_logger_name(self):
        """Whether this class has a 'base_logger_name' attribute."""
        return True


class ATimeComponent(ITimeComponent, AComponent, ABC):
    """Abstract component with time step implementation."""

    def __init__(self):
        super().__init__()
        self._time = None

    @property
    def time(self):
        """The component's current simulation time."""
        try:
            if not isinstance(self._time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise
        return self._time

    @time.setter
    def time(self, time):
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise
        self._time = time


class Input(IInput, Loggable):
    """Default input implementation."""

    def __init__(self):
        self.source = None
        self.base_logger_name = None
        self.name = ""

    def set_source(self, source):
        """Set the input's source output or adapter

        Parameters
        ----------
        source :
            source output or adapter
        """
        # fix to set base-logger for adapters derived from Input source logger
        if isinstance(self, AAdapter):
            if self.uses_base_logger_name and not loggable(source):
                try:
                    raise FinamLogError(
                        f"Adapter '{self.name}' can't get base logger from its source."
                    )
                except FinamLogError as err:
                    self.logger.exception(err)
                    raise
            else:
                self.base_logger_name = source.logger_name
        self.logger.debug("set source")
        try:
            if self.source is not None:
                raise ValueError(
                    "Source of input is already set! "
                    "(You probably tried to connect multiple outputs to a single input)"
                )
            if not isinstance(source, IOutput):
                raise ValueError("Only IOutput can be set as source for Input")
        except ValueError as err:
            self.logger.exception(err)
            raise

        self.source = source

    def get_source(self):
        """Get the input's source output or adapter

        Returns
        -------
        Output
            The input's source.
        """
        self.logger.debug("get source")
        return self.source

    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        self.logger.debug("source changed")

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
        self.logger.debug("pull data")
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

        return self.source.get_data(time)

    @property
    def has_source(self):
        """Flag if this input instance has a source."""
        return self.source is not None

    @property
    def logger_name(self):
        """Logger name derived from base logger name and class name."""
        base_logger = logging.getLogger(self.base_logger_name)
        # logger hierarchy indicated by "." in name
        return ".".join(([base_logger.name, "INPUT", self.name]))

    @property
    def uses_base_logger_name(self):
        """Whether this class has a 'base_logger_name' attribute."""
        return True


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
        self.logger.debug("source changed")
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

        self.callback(self, time)


class Output(IOutput, Loggable):
    """Default output implementation."""

    def __init__(self):
        self.targets = []
        self.data = None
        self.base_logger_name = None
        self.name = ""

    def add_target(self, target):
        """Add a target input or adapter for this output.

        Parameters
        ----------
        target : Input
            The target to add.
        """
        self.logger.debug("add target")
        try:
            if not isinstance(target, IInput):
                raise ValueError("Only IInput can added as target for IOutput")
        except ValueError as err:
            self.logger.exception(err)
            raise

        self.targets.append(target)

    def get_targets(self):
        """Get target inputs and adapters for this output.

        Returns
        -------
        list
            List of targets.
        """
        self.logger.debug("get targets")
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
        self.logger.debug("push data")
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

        self.data = data
        self.notify_targets(time)

    def notify_targets(self, time):
        """Notify all targets by calling their ``source_changed(time)`` method.

        Parameters
        ----------
        time : datetime
            Simulation time of the simulation.
        """
        self.logger.debug("notify targets")
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

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
        any
            data-set for the requested time.
            Should return `None` if no data is available.
        """
        self.logger.debug("get data")
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

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
        self.logger.debug("chain")
        self.add_target(other)
        other.set_source(self)
        return other

    @property
    def has_targets(self):
        """Flag if this output instance has any targets."""
        return bool(self.targets)

    @property
    def logger_name(self):
        """Logger name derived from base logger name and class name."""
        base_logger = logging.getLogger(self.base_logger_name)
        # logger hierarchy indicated by "." in name
        return ".".join(([base_logger.name, "OUTPUT", self.name]))

    @property
    def uses_base_logger_name(self):
        """Whether this class has a 'base_logger_name' attribute."""
        return True


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
        self.logger.debug("push data")
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

        self.notify_targets(time)

    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        self.logger.debug("source changed")
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

        self.notify_targets(time)

    @property
    def name(self):
        """Class name."""
        return self.__class__.__name__

    @name.setter
    def name(self, _):
        pass

    @property
    def logger_name(self):
        """Logger name derived from source logger name and class name."""
        base_logger = logging.getLogger(self.base_logger_name)
        return ".".join(([base_logger.name, "ADAPTER", self.name]))
