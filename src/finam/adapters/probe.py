"""
Adapters for direct probing from link connections.
"""
from ..sdk import Adapter

__all__ = ["CallbackProbe"]


class CallbackProbe(Adapter):
    """Probe data by calling a callback. Simply forwards the data unchanged.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.CallbackProbe(
            callback=lambda data, t: print(data),
        )

    Parameters
    ----------
    callback : callable
        A callback ``callback(data, time)``, returning the transformed data.
    """

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def _get_data(self, time, target):
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
        data = self.pull_data(time, target)
        self.callback(data, time)
        return data
