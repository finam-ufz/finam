from abc import ABC, abstractmethod
from enum import Enum


class ComponentStatus(Enum):
    CREATED = 0
    INITIALIZED = 1
    UPDATED = 2
    FINISHED = 3
    FINALIZED = 4


class IModelComponent(ABC):
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def finalize(self):
        pass

    @abstractmethod
    def time(self):
        pass

    @abstractmethod
    def status(self):
        pass

    @abstractmethod
    def inputs(self):
        pass

    @abstractmethod
    def outputs(self):
        pass


class IInput(ABC):
    @abstractmethod
    def set_source(self, source):
        pass


class IOutput(ABC):
    @abstractmethod
    def add_target(self, target):
        pass

    @abstractmethod
    def get_data(self, time):
        pass


class IAdapter(IInput, IOutput, ABC):
    @abstractmethod
    def set_data(self, data, time):
        pass
