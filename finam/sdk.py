from abc import ABC
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
    def __init__(self):
        self.source = None

    def get_source(self):
        return self.source

    def set_source(self, source):
        self.source = source

    def source_changed(self, time):
        pass

    def pull_data(self, time):
        return self.source.get_data(time)


class Output(IOutput):
    def __init__(self):
        self.targets = []
        self.data = []

    def get_targets(self):
        return self.targets

    def add_target(self, target):
        self.targets.append(target)

    def push_data(self, data, time):
        self.data = data
        self.notify_targets(time)

    def notify_targets(self, time):
        for target in self.targets:
            target.source_changed(time)

    def get_data(self, time):
        return self.data


class AAdapter(IAdapter, Input, Output, ABC):
    def __init__(self):
        super().__init__()
        self.source = None
        self.targets = []
        self.data = []

    def link(self, source, target):
        source.add_target(self)
        self.set_source(source)

        target.set_source(self)
        self.add_target(target)

    def push_data(self, data, time):
        self.notify_targets(time)
