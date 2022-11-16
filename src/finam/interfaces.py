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
        return logging.getLogger(self.logger_name)


class IComponent(ABC):
    """Interface for components."""

    @abstractmethod
    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have :attr:`.status` :attr:`.ComponentStatus.INITIALIZED`.
        """

    @abstractmethod
    def connect(self):
        """Connect exchange data and metadata with linked components.

        The method can be called multiple times if there are failed pull attempts.

        After each method call, the component should have :attr:`.status` :attr:`.ComponentStatus.CONNECTED` if
        connecting was completed, :attr:`.ComponentStatus.CONNECTING` if some but not all required initial input(s)
        could be pulled, and :attr:`.ComponentStatus.CONNECTING_IDLE` if nothing could be pulled.
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

    @abstractmethod
    def set_source(self, source):
        """Set the input's source output or adapter

        Parameters
        ----------
        source :
            source output or adapter
        """

    @abstractmethod
    def get_source(self):
        """Get the input's source output or adapter

        Returns
        -------
        Output
            The input's source.
        """

    @abstractmethod
    def source_updated(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime.datatime
            Simulation time of the notification.
        """

    @abstractmethod
    def pull_data(self, time, target):
        """Retrieve the data from the input's source.

        Parameters
        ----------
        time : datetime.datatime
            Simulation time to get the data for.
        target : IInput or None
            Requesting end point of this pull.

        Returns
        -------
        :class:`xarray.DataArray`
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
        info : Info
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
        target : Input
            The target to add.
        """

    @abstractmethod
    def get_targets(self):
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

        source : IInput
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
        time : datetime.datatime
            Simulation time of the data set.
        """

    @abstractmethod
    def push_info(self, info):
        """Push data info into the output.

        Parameters
        ----------
        info : Info
            Delivered data info
        """

    @abstractmethod
    def notify_targets(self, time):
        """Notify all targets by calling their ``source_updated(time)`` method.

        Parameters
        ----------
        time : datetime.datatime
            Simulation time of the simulation.
        """

    @abstractmethod
    def get_data(self, time, target):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : datetime.datatime
            Simulation time to get the data for.
        target : IInput
            Requesting end point of this pull

        Returns
        -------
        :class:`xarray.DataArray`
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
        info : Info
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
        other : IInput or IAdapter
            The adapter or input to add as target to this output.

        Returns
        -------
        Output
            The last element of the chain.
        """

    def __rshift__(self, other):
        return self.chain(other)


class IAdapter(IInput, IOutput, ABC):
    """Interface for adapters."""


class NoBranchAdapter:
    """Interface to mark adapters as allowing only a single end point."""


class NoDependencyAdapter:
    """Interface to mark adapters as breaking time dependencies between components."""


class ITimeOffsetAdapter:
    """Interface for adapters that manipulate the request time."""

    @abstractmethod
    def with_offset(self, time):
        """Get the manipulated time for a given request time.

        Parameters
        ----------

        time : datetime.datetime
            The original request time.

        Returns
        -------

        datetime.datetime
            The time as manipulated by the adapter
        """
