"""
Interface definitions for the coupling framework.
"""
import logging
from abc import ABC, abstractmethod
from enum import Enum


class FinamStatusError(Exception):
    """Error for wrong status in Component."""


class FinamLogError(Exception):
    """Error for wrong logging configuration."""


class ComponentStatus(Enum):
    """Status for components."""

    CREATED = 0
    INITIALIZED = 1
    CONNECTED = 2
    VALIDATED = 3
    UPDATED = 4
    FINISHED = 5
    FINALIZED = 6


class Loggable(ABC):
    """Loggable component."""

    @property
    @abstractmethod
    def uses_base_logger_name(self):
        """Whether this class has a 'base_logger_name' attribute."""

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
        and the component should have status INITIALIZED.
        """

    @abstractmethod
    def connect(self):
        """Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """

    @abstractmethod
    def validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """

    @abstractmethod
    def update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """

    @abstractmethod
    def finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """

    @property
    @abstractmethod
    def inputs(self):
        """dict: The component's inputs."""

    @property
    @abstractmethod
    def outputs(self):
        """dict: The component's outputs."""

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


class IMpiComponent(ABC):
    """Interface for components which require MPI processes."""

    @abstractmethod
    def run_mpi(self):
        """Run a worker process for the component. This is called for all processes except rank 0.

        Use ``core.mpi.is_null(comm)`` to test if the current process is in the component's communicator.
        """


class IInput(ABC):
    """Interface for input slots."""

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
    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """

    @abstractmethod
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


class IOutput(ABC):
    """Interface for output slots."""

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

    @abstractmethod
    def notify_targets(self, time):
        """Notify all targets by calling their ``source_changed(time)`` method.

        Parameters
        ----------
        time : datetime
            Simulation time of the simulation.
        """

    @abstractmethod
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

    @abstractmethod
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

    def __rshift__(self, other):
        return self.chain(other)


class IAdapter(IInput, IOutput, ABC):
    """Interface for adapters."""


class NoBranchAdapter:
    """Interface to mark adapters as allowing only a single end point."""
