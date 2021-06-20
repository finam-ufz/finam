from sdk import AAdapter


class Callback(AAdapter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def source_changed(self, time):
        self.notify_targets(time)

    def get_data(self, time):
        return self.callback(self.pull_data(time), time)
