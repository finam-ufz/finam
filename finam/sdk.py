from abc import ABC, abstractmethod
from interfaces import IInput, IOutput, IAdapter, IModelComponent


class AModelComponent(IModelComponent, ABC):
    def __init__(self):
        self._inputs = {}
        self._outputs = {}

    def inputs(self):
        return self._inputs

    def outputs(self):
        return self._outputs


class Input(IInput):
    def __init__(self, name):
        self.name = name
        self.source = None

    def get_name(self):
        return self.name

    def get_source(self):
        return self.source

    def set_source(self, source):
        self.source = source

    def pull_data(self, time):
        return self.source.get_data(time)


class Output(IOutput):
    def __init__(self, name):
        self.name = name
        self.targets = []

    def get_name(self):
        return self.name

    def get_targets(self):
        return self.targets

    def add_target(self, target):
        self.targets.append(target)

    def push_data(self, data, time):
        for target in self.targets:
            target.set_data(data, time)


class AAdapter(IAdapter, ABC):
    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def link(self, source, target):
        source.add_target(self)
        target.set_source(self)
