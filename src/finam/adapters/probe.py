"""
Adapters for direct probing from link connections.
"""

from ..core.sdk import AAdapter


class CallbackProbe(AAdapter):
    """Probe data by calling a callback. Simply forwards the data unchanged.

    Parameters
    ----------
    callback : callable
        A callback ``callback(data, time)``, returning the transformed data.
    """

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def get_data(self, time):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : datetime
            simulation time to get the data for.

        Returns
        -------
        array_like
            data-set for the requested time.
        """
        self.logger.debug("get data")
        data = self.pull_data(time)
        self.callback(data, time)
        return data
