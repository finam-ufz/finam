"""
Adapters that deal with time, like temporal interpolation and integration.
"""
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import numpy as np

from finam.interfaces import NoBranchAdapter, NoDependencyAdapter

from ..data import tools as dtools
from ..errors import FinamNoDataError, FinamTimeError
from ..sdk import Adapter, TimeDelayAdapter
from ..tools.date_helper import is_timedelta
from ..tools.log_helper import ErrorLogger

__all__ = [
    "NextTime",
    "PreviousTime",
    "LinearTime",
    "StepTime",
    "StackTime",
    "DelayFixed",
    "DelayToPush",
    "DelayToPull",
    "TimeCachingAdapter",
    "check_time",
    "interpolate",
    "interpolate_step",
]


class DelayFixed(TimeDelayAdapter):
    """Delays/offsets the request time by subtracting a fixed offset.

    Delayed times that are located before the initial pull/request time are set to this time.

    An illustrative example:
    Component A has a step of 10 days.
    The adapter has a delay of 11 days to guarantee data availability in B.

    .. code-block:: Text

        A  O=========O---------o
        ^           .<---------'
        |           V
        B  =O=O=O=O=O

    Parameters
    ----------

    delay : datetime.timedelta
        The delay duration to subtract from the request time.

    See also
    --------

    .adapters.DelayToPull : Delays to use data from a previous pull.
    .adapters.DelayToPush : Delays to use data from the last push.

    """

    def __init__(self, delay):
        super().__init__()

        with ErrorLogger(self.logger):
            if not is_timedelta(delay):
                raise ValueError("Step must be of type timedelta or relativedelta")

        self.delay = delay

    def with_delay(self, time):
        off = time - self.delay
        if off < self.initial_time:
            return self.initial_time

        return off


# pylint: disable=too-many-ancestors
class DelayToPush(TimeDelayAdapter, NoDependencyAdapter):
    """Delays/offsets the request time to the last push time if out of range.

    An illustrative example:
    The adapter delays time to the last available push date.

    .. code-block:: Text

        A  O=========O---------o
        ^               .<-----'
        |               |
        B  =O=O=O=O=O=O=O

    However, if data for the requested time is available, time is not modified:

    .. code-block:: Text

        A  O=========O---------o
        ^                      ^
        |                      |
        B  =O=O=O=O=O=O=O=O=O=O=O

    If the requested time is before the last push, it is not modified.

    .. note::
        This adapters fully breaks dependency chains and loops.

        It is recommended to use other subclasses of :class:`.ITimeDelayAdapter`,
        e.g. :class:`.adapters.DelayFixed` or :class:`.adapters.DelayToPull`.
        These adapters have a more consistent pull interval, and dependencies are still checked.

    See also
    --------

    .adapters.DelayFixed : Delays to use data with a fixed offset.
    .adapters.DelayToPull : Delays to use data from a previous pull.
    """

    def __init__(self):
        super().__init__()
        self.push_time = None

    def with_delay(self, time):
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
        check_time(self.logger, time)
        self.push_time = time


# pylint: disable=too-many-ancestors
class DelayToPull(TimeDelayAdapter, NoBranchAdapter):
    """Delays/offsets the request time to a previous pull time.

    An illustrative example:
    With ``step=2``, the adapter delays time by two past pulls:

    .. code-block:: Text

        A  O====O====O====O----o
        ^            .<--------'
        |            |
        B  =O=O=O=O=O=O=O

    Delay can be fine-tuned by using ``additional_offset`` (e.d. 2 days):

    .. code-block:: Text

        A  O====O====O====O----o
        ^          .<----------'
        |          |
        B  =O=O=O=O=O=O=O

    Parameters
    ----------

    steps : int, optional
        The number of pulls to delay. Defaults to 1.
    additional_delay : datetime.timedelta
        Additional delay in time units. Defaults to no delay.

    See also
    --------

    .adapters.DelayFixed : Delays to use data with a fixed offset.
    .adapters.DelayToPush : Delays to use data from the last push.

    """

    def __init__(self, steps=1, additional_delay=timedelta(days=0)):
        super().__init__()
        self.steps = steps
        self.additional_delay = additional_delay
        self._pulls = []

    def with_delay(self, time):
        if len(self._pulls) == 0:
            self._pulls.append(self.initial_time)

        t = self._pulls[0]
        off = t - self.additional_delay
        if off < self.initial_time:
            return self.initial_time

        return off

    def _pulled(self, time):
        self._pulls.append(time)
        while len(self._pulls) > self.steps:
            self._pulls.pop(0)

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
        d = self.pull_data(time, target)
        return d


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
        check_time(self.logger, time)

        data = dtools.strip_time(self.pull_data(time, self), self._input_info.grid)
        self.data.append((time, self._pack(data)))

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

        check_time(self.logger, time, (self.data[0][0], self.data[-1][0]))

        data = self._interpolate(time)
        self._clear_cached_data(time)
        return data

    def _clear_cached_data(self, time):
        while len(self.data) > 1 and self.data[1][0] <= time:
            d = self.data.pop(0)
            if isinstance(d[1], str):
                os.remove(d[1])
            else:
                self._total_mem -= d[1].nbytes

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
            return self._unpack(self.data[0][1])

        for t, data in self.data:
            if time > t:
                continue

            return self._unpack(data)

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
            return self._unpack(self.data[0][1])

        for i, (t, data) in enumerate(self.data):
            if time > t:
                continue
            if time == t:
                return self._unpack(data)

            _, data_prev = self.data[i - 1]
            return self._unpack(data_prev)

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
                extract.append((t, self._unpack(data)))
                continue

            extract.append((t, self._unpack(data)))
            break

        arr = np.stack([d[1] for d in extract])
        return dtools.prepare(arr, self.info, time_entries=len(extract))


class LinearTime(TimeCachingAdapter):
    """Linear time interpolation.

    .. plot:: api/plots/interpolation-methods.py

        Illustration of interpolation methods.

    See also
    --------

    .adapters.StepTime : Step-wise time interpolation.
    .adapters.AvgOverTime : Average aggregation over time.
    .adapters.SumOverTime : Sum aggregation over time.

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
                return self._unpack(data)

            t_prev, data_prev = self.data[i - 1]

            dt = (time - t_prev) / (t - t_prev)

            result = interpolate(self._unpack(data_prev), self._unpack(data), dt)

            return result

        raise FinamTimeError(
            f"Time interpolation failed. This should not happen and is probably a bug. "
            f"Time is {time}."
        )


class StepTime(TimeCachingAdapter):
    """Step-wise time interpolation.

    .. plot:: api/plots/interpolation-methods.py

        Illustration of interpolation methods.

    Parameters
    ----------

    step : float
        Value in range [0, 1] that determines the relative step position.
        For a value of 0.0, the new value is returned for any dt > 0.0.
        For a value of 1.0, the old value is returned for any dt <= 1.0.
        Values between 0.0 and 1.0 shift the step between the first and the second time.
        A value of 0.5 results in nearest interpolation.

    See also
    --------

    .adapters.LinearTime : Linear time interpolation.
    .adapters.AvgOverTime : Average aggregation over time.
    .adapters.SumOverTime : Sum aggregation over time.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.StepTime(step=0.0)
    """

    def __init__(self, step=0.5):
        super().__init__()
        self.step = step

    def _interpolate(self, time):
        if len(self.data) == 1:
            return self.data[0][1]

        for i, (t, data) in enumerate(self.data):
            if time > t:
                continue
            if time == t:
                return self._unpack(data)

            t_prev, data_prev = self.data[i - 1]

            dt = (time - t_prev) / (t - t_prev)

            result = interpolate_step(data_prev, data, dt, self.step)

            return self._unpack(result)

        raise FinamTimeError(
            f"Time interpolation failed. This should not happen and is probably a bug. "
            f"Time is {time}."
        )


def interpolate(old_value, new_value, dt):
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


def interpolate_step(old_value, new_value, dt, step):
    """Interpolate step-wise between old and new value.

    Parameters
    ----------
    old_value : array_like
        Old value.
    new_value : array_like
        New value.
    dt : float
        Time step between values.
    step : float
        Value in range [0, 1] that determines the relative step position.

        * For a value of 0.0, the new value is returned for any dt > 0.0.
        * For a value of 1.0, the old value is returned for any dt <= 1.0.
        * Values between 0.0 and 1.0 shift the step between the first and the second time.
        * A value of 0.5 results in nearest interpolation.

    Returns
    -------
    array_like
        Interpolated value.
    """
    return new_value if dt > step else old_value


def check_time(logger, time, time_range=(None, None)):
    """
    Checks time.

    Checks time for being of type :class:`datetime <datetime.datetime>`, and to be in range of time_range
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
