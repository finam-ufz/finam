from abstracts import AInput, AOutput, AAdapter, AModelComponent
from interfaces import ComponentStatus


class DummyModel(AModelComponent):
    def __init__(self):
        self.time = 0
        self.status = ComponentStatus.CREATED

    def initialize(self):
        self.status = ComponentStatus.INITIALIZED

    def update(self):
        self.status = ComponentStatus.UPDATED

    def finalize(self):
        self.status = ComponentStatus.FINALIZED

    def time(self):
        return self.time

    def status(self):
        return self.status


if __name__ == "__main__":
    model = DummyModel()

    print(model)
