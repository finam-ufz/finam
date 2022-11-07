"""
Adapters that deal with time, like temporal interpolation and integration.
"""
from datetime import datetime

from finam.interfaces import NoBranchAdapter

from ..data import tools as dtools
from ..errors import FinamNoDataError, FinamTimeError
from ..sdk import Adapter
from ..tools.log_helper import ErrorLogger

__all__ = [
    "ExtrapolateTime",
    "NextTime",
    "PreviousTime",
    "LinearTime",
    "IntegrateTime",
]


class ExtrapolateTime(Adapter, NoBranchAdapter):
    """Time extrapolation (nearest) to break circular dependencies.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.ExtrapolateTime()
    """

    def __init__(self):
        super().__init__()
        self.time = None

    def _source_updated(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        _check_time(self.logger, time)
        self.time = time

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
        _check_time(self.logger, time)

        if self.data is None:
            raise FinamNoDataError(f"No data available in {self.name}")

        t = time if self.time is None or time <= self.time else self.time

        return dtools.strip_data(self.pull_data(t, target))


class NextTime(Adapter):
    """Time interpolation providing the next future value.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.NextTime()
    """

    def __init__(self):
        super().__init__()
        self.data = None
        self.time = None

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

        self.data = self.pull_data(time, self)
        self.time = time

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
        _check_time(self.logger, time, (None, self.time))

        if self.data is None:
            raise FinamNoDataError(f"No data available in {self.name}")

        return self.data


class PreviousTime(Adapter):
    """Time interpolation providing the newest past value.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.PreviousTime()
    """

    def __init__(self):
        super().__init__()
        self.old_data = None
        self.new_data = None

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

        data = self.pull_data(time, self)
        if self.new_data is None:
            self.old_data = (time, data)
        else:
            self.old_data = self.new_data

        self.new_data = (time, data)

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
        _check_time(self.logger, time, (self.old_data[0], self.new_data[0]))

        if self.new_data is None:
            raise FinamNoDataError(f"No data available in {self.name}")

        if time < self.new_data[0]:
            return self.old_data[1]

        return self.new_data[1]


class LinearTime(Adapter):
    """Linear time interpolation.

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.LinearTime()
    """

    def __init__(self):
        super().__init__()
        self.old_data = None
        self.new_data = None

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

        self.old_data = self.new_data
        self.new_data = (time, dtools.strip_data(self.pull_data(time, self)))

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
        if self.new_data is None:
            raise FinamNoDataError(f"No data available in {self.name}")

        _check_time(
            self.logger,
            time,
            (None if self.old_data is None else self.old_data[0], self.new_data[0]),
        )

        if self.old_data is None:
            return self.new_data[1]

        dt = (time - self.old_data[0]) / (self.new_data[0] - self.old_data[0])

        o = self.old_data[1]
        n = self.new_data[1]

        result = _interpolate(o, n, dt)

        return result


class IntegrateTime(Adapter, NoBranchAdapter):
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
        self.data = []
        self.prev_time = None

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

        if len(self.data) > 2:
            self.data = self.data[-2:]

        self.prev_time = time

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
