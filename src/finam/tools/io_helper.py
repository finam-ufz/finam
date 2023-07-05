"""Input and Output helpers."""
import numpy as np

from ..interfaces import IInput, IOutput


def pull_compressed(input, time):
    """
    Pull compressed data from an Input object.

    Parameters
    ----------
    input : IInput
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
        If input is not an IInput instance.
    """
    if not isinstance(input, IInput):
        msg = "pull_compressed: Given input is not an Input object."
        raise ValueError(msg)
    return input.info.grid.to_compressed(input.pull_data(time))


def push_compressed(output, time, data, nodata=np.nan):
    """
    Push compressed data to an Output object.

    Parameters
    ----------
    output : IOutput
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
        If output is not an IOutput instance.
    """
    if not isinstance(output, IOutput):
        msg = "push_compressed: Given output is not an Output object."
        raise ValueError(msg)
    output.push_data(output.info.grid.from_compressed(data, nodata), time)
