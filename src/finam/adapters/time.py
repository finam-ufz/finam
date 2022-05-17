"""
Adapters that deal with time, like temporal interpolation and integration.
"""
from datetime import datetime

from ..core.interfaces import NoBranchAdapter
from ..core.sdk import AAdapter


class NextValue(AAdapter):
    """Time interpolation providing the next future value."""

    def __init__(self):
        super().__init__()
        self.data = None

    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

        data = self.pull_data(time)
        self.data = data

        self.notify_targets(time)

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
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

        return self.data


class PreviousValue(AAdapter):
    """Time interpolation providing the newest past value."""

    def __init__(self):
        super().__init__()
        self.old_data = None
        self.new_data = None

    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

        data = self.pull_data(time)
        if self.new_data is None:
            self.old_data = (time, data)
        else:
            self.old_data = self.new_data

        self.new_data = (time, data)

        self.notify_targets(time)

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
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

        if time < self.new_data[0]:
            return self.old_data[1]

        return self.new_data[1]


class LinearInterpolation(AAdapter):
    """Linear time interpolation."""

    def __init__(self):
        super().__init__()
        self.old_data = None
        self.new_data = None

    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        self.old_data = self.new_data
        self.new_data = (time, self.pull_data(time))

        self.notify_targets(time)

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
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

        if self.old_data is None:
            return self.new_data[1]

        dt = (time - self.old_data[0]) / (self.new_data[0] - self.old_data[0])

        o = self.old_data[1]
        n = self.new_data[1]

        return _interpolate(o, n, dt)


class LinearIntegration(AAdapter, NoBranchAdapter):
    """Time integration over the last time step of the requester.

    Calculates the temporal average.
    """

    def __init__(self):
        super().__init__()
        self.data = []
        self.prev_time = None

    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        data = self.pull_data(time)
        self.data.append((time, data))

        if self.prev_time is None:
            self.prev_time = time

        self.notify_targets(time)

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
        try:
            if not isinstance(time, datetime):
                raise ValueError("Time must be of type datetime")
        except ValueError as err:
            self.logger.exception(err)
            raise

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
