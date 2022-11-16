"""
Adapters that deal with time, like temporal interpolation and integration.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import numpy as np

from finam.interfaces import NoBranchAdapter

from ..data import tools as dtools
from ..errors import FinamNoDataError, FinamTimeError
from ..sdk import Adapter, TimeOffsetAdapter
from ..tools.log_helper import ErrorLogger

__all__ = [
    "NextTime",
    "PreviousTime",
    "LinearTime",
    "IntegrateTime",
    "StackTime",
    "OffsetFixed",
    "OffsetToPush",
    "TimeCachingAdapter",
]


class OffsetFixed(TimeOffsetAdapter):
    """Offsets the request time by subtracting a fixed offset.

    Offset results that are located before the initial pull/request time are set to this time.

    An illustrative example:
    Component A has a step of 10 days.
    The adapter has an offset of 11 days to guarantee data availability in B.

    .. code-block:: Text

        A  O=========O---------o
        ^           .<---------'
        |           V
        B  =O=O=O=O=O

    Parameters
    ----------

    offset : datetime.timedelta
        The offset duration to subtract from the request time.
    """

    def __init__(self, offset):
        super().__init__()

        with ErrorLogger(self.logger):
            if not isinstance(offset, timedelta):
                raise ValueError("Step must be of type timedelta")

        self.offset = offset

    def with_offset(self, time):
        off = time - self.offset
        if off < self.initial_time:
            return self.initial_time

        return off


class OffsetToPush(TimeOffsetAdapter):
    """Offsets the request time to the last push time of out of range.

    An illustrative example:
    The adapter offsets time to the last available push date.

    .. code-block:: Text

        A  O=========O---------o
        ^               .<-----'
        |               |
        B  =O=O=O=O=O=O=O

    However, if data for the requested time is available, time is not  modified:

    .. code-block:: Text

        A  O=========O---------o
        ^                      ^
        |                      |
        B  O=O=O=O=O=O=O=OO=O=O=O

    If the requested time is before the last push, it is not modified.
    """

    def __init__(self):
        super().__init__()
        self.push_time = None

    def with_offset(self, time):
        if self.push_time is None:
            return self.initial_time

        if time > self.push_time:
            return self.push_time

        return time

    def _source_updated(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        _check_time(self.logger, time)
        self.push_time = time


class TimeCachingAdapter(Adapter, NoBranchAdapter, ABC):
    """Abstract base class for time handling and caching adapters."""

    def __init__(self):
        super().__init__()
        self.data = []

    @property
    def needs_push(self):
        return True

    def _source_updated(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        _check_time(self.logger, time)

        data = dtools.strip_data(self.pull_data(time, self))
        self.data.append((time, data))

    def _get_data(self, time, _target):
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
        if len(self.data) == 0:
            raise FinamNoDataError(f"No data available in {self.name}")

        _check_time(self.logger, time, (self.data[0][0], self.data[-1][0]))

        data = self._interpolate(time)
        self._clear_cached_data(time)
        return data

    def _clear_cached_data(self, time):
        while len(self.data) > 1 and self.data[1][0] <= time:
            self.data.pop(0)

    @abstractmethod
    def _interpolate(self, time):
        """Interpolate for the given time"""


class NextTime(TimeCachingAdapter):
    """Time interpolation providing the next future value.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.NextTime()
    """

    def _interpolate(self, time):
        if len(self.data) == 1:
            return self.data[0][1]

        for t, data in self.data:
            if time > t:
                continue

            return data

        raise FinamTimeError(
            f"Time interpolation failed. This should not happen and is probably a bug. "
            f"Time is {time}."
        )


class PreviousTime(TimeCachingAdapter):
    """Time interpolation providing the newest past value.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.PreviousTime()
    """

    def _interpolate(self, time):
        if len(self.data) == 1:
            return self.data[0][1]

        for i, (t, data) in enumerate(self.data):
            if time > t:
                continue
            if time == t:
                return data

            _, data_prev = self.data[i - 1]
            return data_prev

        raise FinamTimeError(
            f"Time interpolation failed. This should not happen and is probably a bug. "
            f"Time is {time}."
        )


class StackTime(TimeCachingAdapter):
    """Stacks all incoming data since the last push.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.StackTime()
    """

    def _interpolate(self, time):
        extract = []

        for t, data in self.data:
            if time > t:
                extract.append((t, data))
                continue

            extract.append((t, data))
            break

        arr = np.stack([d[1] for d in extract])
        return dtools.to_xarray(arr, self.name, self.info, [d[0] for d in extract])


class LinearTime(TimeCachingAdapter):
    """Linear time interpolation.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.LinearTime()
    """

    def _interpolate(self, time):

        if len(self.data) == 1:
            return self.data[0][1]

        for i, (t, data) in enumerate(self.data):
            if time > t:
                continue
            if time == t:
                return data

            t_prev, data_prev = self.data[i - 1]

            dt = (time - t_prev) / (t - t_prev)

            result = _interpolate(data_prev, data, dt)

            return result

        raise FinamTimeError(
            f"Time interpolation failed. This should not happen and is probably a bug. "
            f"Time is {time}."
        )


class IntegrateTime(TimeCachingAdapter):
    """Time integration over the last time step of the requester.

    Calculates the temporal average.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.IntegrateTime()

    """

    def __init__(self):
        super().__init__()
        self.prev_time = None

    def _source_updated(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        _check_time(self.logger, time)

        data = dtools.strip_data(self.pull_data(time, self))
        self.data.append((time, data))

        if self.prev_time is None:
            self.prev_time = time

    def _get_data(self, time, _target):
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
        if len(self.data) == 0:
            raise FinamNoDataError(f"No data available in {self.name}")

        _check_time(self.logger, time, (self.data[0][0], self.data[-1][0]))

        sum_value = self._interpolate(time)
        self._clear_cached_data(self.prev_time)
        self.prev_time = time
        return sum_value

    def _interpolate(self, time):

        if len(self.data) == 1:
            return self.data[0][1]

        if time <= self.data[0][0]:
            return self.data[0][1]

        sum_value = None

        for i in range(len(self.data) - 1):
            t_old, v_old = self.data[i]
            t_new, v_new = self.data[i + 1]

            if self.prev_time >= t_new:
                continue
            if time <= t_old:
                break

            scale = t_new - t_old

            dt1 = max((self.prev_time - t_old) / scale, 0.0)
            dt2 = min((time - t_old) / scale, 1.0)

            v1 = _interpolate(v_old, v_new, dt1)
            v2 = _interpolate(v_old, v_new, dt2)
            value = (dt2 - dt1) * scale.total_seconds() * 0.5 * (v1 + v2)

            sum_value = value if sum_value is None else sum_value + value

        dt = time - self.prev_time
        if dt.total_seconds() > 0:
            sum_value /= dt.total_seconds()

        return sum_value


def _interpolate(old_value, new_value, dt):
    """Interpolate between old and new value.

    Parameters
    ----------
    old_value : array_like
        Old value.
    new_value : array_like
        New value.
    dt : float
        Time step between values.

    Returns
    -------
    array_like
        Interpolated value.
    """
    return old_value + dt * (new_value - old_value)


def _check_time(logger, time, time_range=(None, None)):
    """
    Checks time.

    Checks time for being of type `datetime`, and to be in range of time_range
    (upper and lower limits inclusive).

    Parameters
    ----------
    logger : logging.Logger
        Logger to print to
    time : any
        Time to be tested
    time_range : tuple, optional
        Tuple of (min, max) time, elements can be `None`, by default (None, None)

    Raises
    ------
    FinamTimeError
        if any of the checks fails
    """
    with ErrorLogger(logger):
        if not isinstance(time, datetime):
            raise FinamTimeError("Time must be of type datetime")

        if time_range[1] is not None and time > time_range[1]:
            raise FinamTimeError(
                "Requested data for time point in the future. "
                f"Latest data: {time_range[1]}, request: {time}"
            )

        if time_range[0] is not None and time < time_range[0]:
            raise FinamTimeError(
                "Requested data for time point in the past. "
                f"Earliest data: {time_range[0]}, request: {time}"
            )
