from core.sdk import AAdapter


class Callback(AAdapter):
    """
    Transform data using a callback.
    """

    def __init__(self, callback):
        """
        Create a new Callback generator.

        :param callback: A callback ``callback(data, time)``
        """
        super().__init__()
        self.callback = callback

    def get_data(self, time):
        return self.callback(self.pull_data(time), time)
