"""
Adapters for direct probing from link connections.
"""

from core.sdk import AAdapter


class CallbackProbe(AAdapter):
    """
    Probe data by calling a callback. Simply forwards the data unchanged.
    """

    def __init__(self, callback):
        """
        Create a new Callback generator.

        :param callback: A callback ``callback(data, time)``, returning nothing.
        """
        super().__init__()
        self.callback = callback

    def get_data(self, time):
        data = self.pull_data(time)
        self.callback(data, time)
        return data
