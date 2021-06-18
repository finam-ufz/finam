from abc import ABC, abstractmethod
from interfaces import IInput, IOutput, IAdapter, IModelComponent


class AModelComponent(IModelComponent, ABC):
    def __init__(self):
        self.inputs = {}
        self.outputs = {}

    def inputs(self):
        return self.inputs

    def outputs(self):
        return self.outputs


class AInput(IInput, ABC):
    def __init__(self):
        self.source = None

    def set_source(self, source):
        self.source = source


class AOutput(IOutput, ABC):
    def __init__(self):
        self.targets = []

    def add_target(self, target):
        self.targets.append(target)

    @abstractmethod
    def get_data(self, time):
        pass


class AAdapter(IAdapter, AOutput, ABC):
    @abstractmethod
    def set_data(self, data, time):
        pass
