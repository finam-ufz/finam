"""
Implementations of the coupling interfaces for simpler development of modules and adapters.
"""
import logging
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
        self._base_logger_name = None

    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        self.logger.debug("init")
        try:
            if self._status != ComponentStatus.CREATED:
                raise FinamStatusError(
                    f"Unexpected model state {self._status} in {self.name}"
                )
        except FinamStatusError as err:
            self.logger.exception(err)
            raise

    def connect(self):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        self.logger.debug("connect")
        try:
            if self._status != ComponentStatus.INITIALIZED:
                raise FinamStatusError(
                    f"Unexpected model state {self._status} in {self.name}"
                )
        except FinamStatusError as err:
            self.logger.exception(err)
            raise

    def validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """
        self.logger.debug("validate")
        try:
            if self._status != ComponentStatus.CONNECTED:
                raise FinamStatusError(
                    f"Unexpected model state {self._status} in {self.name}"
                )
        except FinamStatusError as err:
            self.logger.exception(err)
            raise

    def update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        self.logger.debug("update")
        try:
            if not self._status in (ComponentStatus.VALIDATED, ComponentStatus.UPDATED):
                raise FinamStatusError(
                    f"Unexpected model state {self._status} in {self.name}"
                )
        except FinamStatusError as err:
            self.logger.exception(err)
            raise

    def finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
        self.logger.debug("finalize")
        try:
            if not self._status in (ComponentStatus.UPDATED, ComponentStatus.FINISHED):
                raise FinamStatusError(
                    f"Unexpected model state {self._status} in {self.name}"
                )
        except FinamStatusError as err:
            self.logger.exception(err)
            raise

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

    @property
    def name(self):
        """Component name."""
        return self.__class__.__name__

    @property
    def logger_name(self):
        """Logger name derived from base logger name and class name."""
        base_logger = logging.getLogger(self._base_logger_name)
        # logger hierarchy indicated by "." in name
        return ".".join(([base_logger.name, self.name]))

    @property
    def logger(self):
        """Logger for this component."""
        return logging.getLogger(self.logger_name)


class ATimeComponent(ITimeComponent, AComponent, ABC):
    """Abstract component with time step implementation."""

    def __init__(self):
        super().__init__()
        self._time = None
        self._base_logger_name = None

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


class Input(IInput):
    """Default input implementation."""

    def __init__(self):
        self.source = None
        self._base_logger_name = None
        self._name = ""

    def set_source(self, source):
        """Set the input's source output or adapter

        Parameters
        ----------
        source :
            source output or adapter
        """
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
    def name(self):
        """Input name."""
        return self._name

    @property
    def logger_name(self):
        """Logger name derived from base logger name and class name."""
        base_logger = logging.getLogger(self._base_logger_name)
        # logger hierarchy indicated by "." in name
        return ".".join(([base_logger.name, "INPUT", self.name]))

    @property
    def logger(self):
        """Logger for this component."""
        return logging.getLogger(self.logger_name)


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


class Output(IOutput):
    """Default output implementation."""

    def __init__(self):
        self.targets = []
        self.data = []
        self._base_logger_name = None
        self._name = ""

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
        array_like
            data-set for the requested time.
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
    def name(self):
        """Output name."""
        return self._name

    @property
    def logger_name(self):
        """Logger name derived from base logger name and class name."""
        base_logger = logging.getLogger(self._base_logger_name)
        # logger hierarchy indicated by "." in name
        return ".".join(([base_logger.name, "OUTPUT", self.name]))

    @property
    def logger(self):
        """Logger for this component."""
        return logging.getLogger(self.logger_name)


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

    @property
    def logger_name(self):
        """Logger name derived from source logger name and class name."""
        # TODO: could at some point self.source be None if logger is called?
        return ".".join(([self.source.logger_name, "ADAPTER", self.name]))
