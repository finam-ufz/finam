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


class AInput(IInput, ABC):
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


class AOutput(IOutput, ABC):
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
        self.source = None
        self.targets = []

    def get_name(self):
        return self.name

    def get_source(self):
        return self.source

    def set_source(self, source):
        self.source = source

    def get_targets(self):
        return self.targets

    def add_target(self, target):
        self.targets.append(target)

    def link(self, source, target):
        self.set_source(source)
        source.add_target(self)

        self.add_target(target)
        target.set_source(self)

    def push_data(self, data, time):
        pass
