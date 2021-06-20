from abc import ABC, abstractmethod
from enum import Enum


class ComponentStatus(Enum):
    CREATED = 0
    INITIALIZED = 1
    VALIDATED = 2
    UPDATED = 3
    FINISHED = 4
    FINALIZED = 5


class IModelComponent(ABC):
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def validate(self):
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
    def get_source(self):
        pass

    @abstractmethod
    def set_source(self, source):
        pass

    @abstractmethod
    def source_changed(self, time):
        pass

    @abstractmethod
    def pull_data(self, time):
        pass


class IOutput(ABC):
    @abstractmethod
    def get_targets(self):
        pass

    @abstractmethod
    def add_target(self, target):
        pass

    @abstractmethod
    def push_data(self, data, time):
        pass

    @abstractmethod
    def notify_targets(self, time):
        pass

    @abstractmethod
    def get_data(self, time):
        pass


class IAdapter(IInput, IOutput, ABC):
    pass
