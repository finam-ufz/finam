"""
Interface definitions for the coupling framework.
"""

from abc import ABC, abstractmethod
from enum import Enum


class ComponentStatus(Enum):
    """
    Status for components.
    """

    CREATED = 0
    INITIALIZED = 1
    CONNECTED = 2
    VALIDATED = 3
    UPDATED = 4
    FINISHED = 5
    FINALIZED = 6


class IModelComponent(ABC):
    """
    Interface for model components.
    """

    @abstractmethod
    def initialize(self):
        """
        Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        pass

    @abstractmethod
    def connect(self):
        """
        Push initial values to outputs.

        After the method call, the component should have status CONNECTED.
        """
        pass

    @abstractmethod
    def validate(self):
        """
        Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """
        pass

    @abstractmethod
    def update(self):
        """
        Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        pass

    @abstractmethod
    def finalize(self):
        """
        Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
        pass

    @abstractmethod
    def time(self):
        """
        The component's current simulation time.

        :return: current time stamp
        """
        pass

    @abstractmethod
    def status(self):
        """
        The component's current status.

        :return: current status (a ``ComponentStatus``)
        """
        pass

    @abstractmethod
    def inputs(self):
        """
        The component's inputs.

        :return: dictionary of inputs by name
        """
        pass

    @abstractmethod
    def outputs(self):
        """
        The component's outputs.

        :return: dictionary of outputs by name
        """
        pass


class IInput(ABC):
    """
    Interface for input slots.
    """

    @abstractmethod
    def set_source(self, source):
        """
        Set the input's source output or adapter

        :param source: source output or adapter
        """
        pass

    @abstractmethod
    def source_changed(self, time):
        """
        Informs the input that a new output is available.

        :param time: simulation time of the notification
        """
        pass

    @abstractmethod
    def pull_data(self, time):
        """
        Retrieve the data from the input's source.

        :param time: simulation time to get the data for
        :return: data set fot the given simulation time
        """
        pass


class IOutput(ABC):
    """
    Interface for output slots.
    """

    @abstractmethod
    def add_target(self, target):
        """
        Add a target input or adapter for this output.

        :param target: the target to add
        """
        pass

    @abstractmethod
    def push_data(self, data, time):
        """
        Push data into the output.
        Should notify targets, and can handle the provided date.

        :param data: data set to push
        :param time: simulation time of the data set
        """
        pass

    @abstractmethod
    def notify_targets(self, time):
        """
        Notify all targets by calling their ``source_changed(time)`` method.

        :param time: simulation time of the simulation
        """
        pass

    @abstractmethod
    def get_data(self, time):
        """
        Get the output's data-set for the given time

        :param time: simulation time to get the data for
        :return: data-set for the requested time
        """
        pass

    @abstractmethod
    def chain(self, other):
        """
        Chain outputs and adapters

        :param other: the adapter or output to add as target to this output
        :return: the last element of the chain
        """
        pass

    def __rshift__(self, other):
        """
        Chain outputs and adapters

        :param other: the adapter or output to add as target to this output
        :return: the last element of the chain
        """
        return self.chain(other)


class IAdapter(IInput, IOutput, ABC):
    """
    Interface for adapters.
    """

    pass
