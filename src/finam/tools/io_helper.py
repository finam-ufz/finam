"""Input and Output helpers."""
import numpy as np

from ..interfaces import IInput, IOutput


def pull_compressed(io, time):
    """
    Pull compressed data from an Input object.

    Parameters
    ----------
    io : IInput
        The Input object to pull data from.
    time : :class:`datetime <datetime.datetime>`
        Simulation time to get the data for.

    Returns
    -------
    :class:`pint.Quantity`
        Flattened and unmasked data values for the given simulation time.

    Raises
    ------
    ValueError
        If io is not an IInput instance.
    """
    if not isinstance(io, IInput):
        msg = "pull_compressed: Given io-object is not an IInput instance."
        raise ValueError(msg)
    return io.info.grid.to_compressed(io.pull_data(time))


def push_compressed(io, time, data, nodata=np.nan):
    """
    Push compressed data to an Output object.

    Parameters
    ----------
    io : IOutput
        The Output object to push data to.
    time : :class:`datetime <datetime.datetime>`
        Simulation time of the data set.
    data : array_like
        Flattened and unmasked data values to push.
    nodata : numeric, optional
        Fill value for masked values. Should have a compatible type.
        By default np.nan

    Raises
    ------
    ValueError
        If io is not an IOutput instance.
    """
    if not isinstance(io, IOutput):
        msg = "push_compressed: Given io-object is not an IOutput instance."
        raise ValueError(msg)
    io.push_data(io.info.grid.from_compressed(data, nodata), time)
