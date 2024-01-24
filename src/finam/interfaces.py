"""
Interface definitions for the coupling framework.

Interfaces
==========

.. autosummary::
   :toctree: generated

    :noindex: IComponent
    :noindex: ITimeComponent
    :noindex: IAdapter
    :noindex: IInput
    :noindex: IOutput
    :noindex: ComponentStatus
    :noindex: Loggable
    :noindex: NoBranchAdapter
"""
import logging
from abc import ABC, abstractmethod
from enum import Enum


class ComponentStatus(Enum):
    """Status for components."""

    CREATED = 0
    INITIALIZED = 1
    CONNECTING = 2
    CONNECTING_IDLE = 3
    CONNECTED = 4
    VALIDATED = 5
    UPDATED = 6
    FINISHED = 7
    FINALIZED = 8
    FAILED = 9


class Loggable(ABC):
    """Loggable component."""

    @abstractmethod
    def __init__(self):
        self._logger = None

    @property
    @abstractmethod
    def uses_base_logger_name(self):
        """Whether this class has a ``base_logger_name`` attribute."""

    @property
    @abstractmethod
    def logger_name(self):
        """Logger name."""

    @property
    def logger(self):
        """Logger for this component."""
        if self._logger is None:
            if (
                self.uses_base_logger_name
                and hasattr(self, "base_logger_name")
                and getattr(self, "base_logger_name") is None
            ):
                return logging.getLogger(self.logger_name)
            self._logger = logging.getLogger(self.logger_name)
        return self._logger


class IComponent(ABC):
    """Interface for components."""

    @abstractmethod
    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have :attr:`.status` :attr:`.ComponentStatus.INITIALIZED`.
        """

    @abstractmethod
    def connect(self, start_time):
        """Connect exchange data and metadata with linked components.

        The method can be called multiple times if there are failed pull attempts.

        After each method call, the component should have :attr:`.status` :attr:`.ComponentStatus.CONNECTED` if
        connecting was completed, :attr:`.ComponentStatus.CONNECTING` if some but not all required initial input(s)
        could be pulled, and :attr:`.ComponentStatus.CONNECTING_IDLE` if nothing could be pulled.

        Parameters
        ----------
        start_time : :class:`datetime <datetime.datetime>`
            The composition's starting time.
            Can be before the component's actual time.
        """

    @abstractmethod
    def validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have :attr:`.status` :attr:`.ComponentStatus.VALIDATED`.
        """

    @abstractmethod
    def update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have :attr:`.status`
        :attr:`.ComponentStatus.UPDATED` or :attr:`.ComponentStatus.FINISHED`.
        """

    @abstractmethod
    def finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have :attr:`.status` :attr:`.ComponentStatus.FINALIZED`.
        """

    @property
    @abstractmethod
    def name(self):
        """Component name."""

    @property
    @abstractmethod
    def inputs(self):
        """IOList: The component's inputs."""

    @property
    @abstractmethod
    def outputs(self):
        """IOList: The component's outputs."""

    @property
    @abstractmethod
    def status(self):
        """The component's current status."""

    @property
    @abstractmethod
    def metadata(self):
        """
        The component's meta data.
        Will only be called after the connect phase of the composition.
        """


class ITimeComponent(IComponent, ABC):
    """Interface for components with a time step."""

    @property
    @abstractmethod
    def time(self):
        """The component's current simulation time."""

    @property
    @abstractmethod
    def next_time(self):
        """The component's predicted simulation time of the next pulls.

        Can be ``None`` if the component has no inputs.
        """


class IInput(ABC):
    """Interface for input slots."""

    @property
    @abstractmethod
    def name(self):
        """Input name."""

    @property
    @abstractmethod
    def is_static(self):
        """Whether the input is static"""

    @property
    @abstractmethod
    def info(self):
        """Info: The input's data info."""

    @property
    @abstractmethod
    def needs_pull(self):
        """bool: if the input needs pull."""

    @property
    @abstractmethod
    def needs_push(self):
        """bool: if the input needs push."""

    @property
    @abstractmethod
    def source(self):
        """Get the input's source output or adapter

        Returns
        -------
        :class:`.IOutput`
            The input's source.
        """

    @source.setter
    @abstractmethod
    def source(self, source):
        """Set the input's source output or adapter

        Parameters
        ----------
        source : :class:`.IOutput`
            source output or adapter
        """

    @abstractmethod
    def source_updated(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time of the notification.
        """

    @abstractmethod
    def pull_data(self, time, target):
        """Retrieve the data from the input's source.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time to get the data for.
        target : :class:`.IInput` or None
            Requesting end point of this pull.

        Returns
        -------
        :class:`pint.Quantity`
            Data set for the given simulation time.
        """

    @abstractmethod
    def ping(self):
        """Pings upstream to inform outputs about the number of connected inputs.

        Must be called after linking and before the connect phase.
        """

    @abstractmethod
    def exchange_info(self, info):
        """Exchange the data info with the input's source.

        Parameters
        ----------
        info : :class:`.Info`
            request parameters

        Returns
        -------
        dict
            delivered parameters
        """


class IOutput(ABC):
    """Interface for output slots."""

    @property
    @abstractmethod
    def name(self):
        """Output name."""

    @property
    @abstractmethod
    def time(self):
        """The output's time of the latest available data"""

    @property
    @abstractmethod
    def is_static(self):
        """Whether the output is static"""

    @property
    @abstractmethod
    def info(self):
        """Info: The output's data info.

        Raises
        ------
        FinamNoDataError
            Raises the error if infos were not yet exchanged
        """

    @property
    @abstractmethod
    def needs_pull(self):
        """bool: if the output needs pull."""

    @property
    @abstractmethod
    def needs_push(self):
        """bool: if the output needs push."""

    @property
    @abstractmethod
    def memory_limit(self):
        """The memory limit for this slot"""

    @memory_limit.setter
    @abstractmethod
    def memory_limit(self, limit):
        """The memory limit for this slot"""

    @property
    @abstractmethod
    def memory_location(self):
        """The memory-mapping location for this slot"""

    @memory_location.setter
    @abstractmethod
    def memory_location(self, directory):
        """The memory-mapping location for this slot"""

    @abstractmethod
    def has_info(self):
        """Returns if the output has a data info.

        The info is not required to be validly exchanged.
        """

    @abstractmethod
    def add_target(self, target):
        """Add a target input or adapter for this output.

        Parameters
        ----------
        target : :class:`.IInput`
            The target to add.
        """

    @property
    @abstractmethod
    def targets(self):
        """Get target inputs and adapters for this output.

        Returns
        -------
        list
            List of targets.
        """

    @abstractmethod
    def pinged(self, source):
        """Called when receiving a ping from a downstream input.

        Parameters
        ----------

        source : :class:`.IInput`
            Pinging target end point
        """

    @abstractmethod
    def push_data(self, data, time):
        """Push data into the output.

        Should notify targets, and can handle the provided date.

        Parameters
        ----------
        data : array_like
            Data set to push.
        time : :class:`datetime <datetime.datetime>`
            Simulation time of the data set.
        """

    @abstractmethod
    def push_info(self, info):
        """Push data info into the output.

        Parameters
        ----------
        info : :class:`.Info`
            Delivered data info
        """

    @abstractmethod
    def notify_targets(self, time):
        """Notify all targets by calling their ``source_updated(time)`` method.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time of the simulation.
        """

    @abstractmethod
    def get_data(self, time, target):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time to get the data for.
        target : :class:`.IInput`
            Requesting end point of this pull

        Returns
        -------
        :class:`pint.Quantity`
            data-set for the requested time.

        Raises
        ------
        FinamNoDataError
            Raises the error if no data is available
        """

    @abstractmethod
    def get_info(self, info):
        """Exchange and get the output's data info.

        Parameters
        ----------
        info : :class:`.Info`
            Requested data info

        Returns
        -------
        dict
            Delivered data info

        Raises
        ------
        FinamNoDataError
            Raises the error if no info is available
        """

    @abstractmethod
    def chain(self, other):
        """Chain outputs and adapters.

        Parameters
        ----------
        other : :class:`.IInput` or :class:`.IAdapter`
            The adapter or input to add as target to this output.

        Returns
        -------
        :class:`.IOutput`
            The last element of the chain.
        """

    @abstractmethod
    def finalize(self):
        """Finalize the output"""

    def __rshift__(self, other):
        return self.chain(other)


class IAdapter(IInput, IOutput, ABC):
    """Interface for adapters."""

    @property
    @abstractmethod
    def metadata(self):
        """
        The adapter's meta data.
        Will only be called after the connect phase of the composition.
        """


class NoBranchAdapter:
    """Interface to mark adapters as allowing only a single end point."""


class NoDependencyAdapter:
    """Interface to mark adapters as breaking time dependencies between components."""


class ITimeDelayAdapter(ABC):
    """Interface for adapters that manipulate the request time."""

    @abstractmethod
    def with_delay(self, time):
        """Get the manipulated time for a given request time.

        Parameters
        ----------

        time : :class:`datetime <datetime.datetime>`
            The original request time.

        Returns
        -------

        :class:`datetime <datetime.datetime>`
            The time as manipulated by the adapter
        """
