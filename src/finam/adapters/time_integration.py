"""Adapters for time integration"""
from abc import ABC
from datetime import timedelta

from ..data import tools
from ..errors import FinamNoDataError
from .time import TimeCachingAdapter, check_time, interpolate


class TimeIntegrationAdapter(TimeCachingAdapter, ABC):
    """Abstract base class for time integration adapters."""

    def __init__(self):
        super().__init__()
        self._prev_time = None
        self._info = None

    def _source_updated(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        check_time(self.logger, time)

        data = tools.strip_data(self.pull_data(time, self))
        self.data.append((time, data))

        if self._prev_time is None:
            self._prev_time = time

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

        sum_value = self._interpolate(time)
        self._clear_cached_data(self._prev_time)
        self._prev_time = time
        return sum_value


# pylint: disable=too-many-ancestors
class AvgOverTime(TimeIntegrationAdapter):
    """Aggregates data over time to form the temporal average over the last pull time step.

    Can use step-wise or linear interpolation between push time steps.

    .. code-block:: Text

        linear (step=None)
           .o.         .o
          /   \\       /
        o'     'o---o'

        step=0.0
        +---o       +---o
        |   |       |
        o   +---o---o

        step=0.5
          +-o-+       +-o
          |   |       |
        o-+   +-o---o-+

        step=1.0
            o---+       o
            |   |       |
        o---+   o---o---+

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.AvgOverTime()

    Parameters
    ----------

    step : float, optional
        Value in range [0, 1] that determines the relative step position.

        Linear interpolation is used if set to ``None`` (the default).

        * For a value of 0.0, the new value is returned for any dt > 0.0.
        * For a value of 1.0, the old value is returned for any dt <= 1.0.
        * Values between 0.0 and 1.0 shift the step between the first and the second time.
        * A value of 0.5 results in nearest interpolation.
    """

    def __init__(self, step=None):
        super().__init__()
        self._prev_time = None
        self._step = step
        self._info = None

    def _interpolate(self, time):
        if len(self.data) == 1:
            return self.data[0][1]

        if time <= self.data[0][0]:
            return self.data[0][1]

        sum_value = None

        for i in range(len(self.data) - 1):
            t_old, v_old = self.data[i]
            t_new, v_new = self.data[i + 1]

            if self._prev_time >= t_new:
                continue
            if time <= t_old:
                break

            time_range = t_new - t_old

            dt1 = max((self._prev_time - t_old) / time_range, 0.0)
            dt2 = min((time - t_old) / time_range, 1.0)

            if self._step is None:
                v1 = interpolate(v_old, v_new, dt1)
                v2 = interpolate(v_old, v_new, dt2)
                value = (dt2 - dt1) * 0.5 * (v1 + v2)
            else:
                dt1 = min(dt1, self._step)
                dt2 = max(self._step, dt2)
                value = (self._step - dt1) * v_old + (dt2 - self._step) * v_new

            value *= time_range.total_seconds() * tools.UNITS.Unit("s")

            sum_value = value if sum_value is None else sum_value + value

        dt = time - self._prev_time
        if dt.total_seconds() > 0:
            sum_value /= dt.total_seconds() * tools.UNITS.Unit("s")

        return sum_value


# pylint: disable=too-many-ancestors
class SumOverTime(TimeIntegrationAdapter):
    """Aggregates data over time to form the temporal sum (area under curve) over the last pull time step.

    Can use step-wise or linear interpolation between push time steps.

    .. code-block:: Text

        linear (step=None)
           .o.         .o
          /   \\       /
        o'     'o---o'

        step=0.0
        +---o       +---o
        |   |       |
        o   +---o---o

        step=0.5
          +-o-+       +-o
          |   |       |
        o-+   +-o---o-+

        step=1.0
            o---+       o
            |   |       |
        o---+   o---o---+

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        adapter = fm.adapters.SumOverTime()

    Parameters
    ----------

    step : float, optional
        Value in range [0, 1] that determines the relative step position.
        Defaults to 0.0, which means values are interpreted as constant over each time step.

        Linear interpolation is used if set to ``None``.

        * For a value of 0.0, the new value is returned for any dt > 0.0.
        * For a value of 1.0, the old value is returned for any dt <= 1.0.
        * Values between 0.0 and 1.0 shift the step between the first and the second time.
        * A value of 0.5 results in nearest interpolation.
    per_time : bool, optional
        Whether the input data is time-normalized.

        Use ``True`` for input units like mm/d e.g. for precipitation.
        Data per step is multiplied with step length, with time cancelling out:
        mm/d becomes mm.

        Use ``False`` for absolute amount, e.g. mm for the precipitation of the last time step.
        Output will be the same as input units. Duration of time steps is not explicitly taken into account.

        Examples:

        * ``per_time=True``, value=1mm/d, step=2x5d --> 10 mm
        * ``per_time=True``, value=1mm, step=2x5d --> 10mm*d
        * ``per_time=False``, value=1mm/d, step=2x5d --> 2mm/d
        * ``per_time=False``, value=1mm, step=2x5d --> 2mm

    initial_interval: :class:`datetime <datetime.datetime>`, optional
        Time scaling duration for the initial data. Defaults to 0 days.

    """

    def __init__(self, step=0.0, per_time=True, initial_interval=timedelta(0)):
        super().__init__()
        self._prev_time = None
        self._step = step
        self._per_time = per_time
        self._initial_interval = initial_interval

        self._info = None

    def _interpolate(self, time):
        if len(self.data) == 1 or time <= self.data[0][0]:
            if self._per_time:
                return (
                    self.data[0][1]
                    * self._initial_interval.total_seconds()
                    * tools.UNITS.Unit("s")
                ).to_reduced_units()

            return self.data[0][1]

        sum_value = None

        for i in range(len(self.data) - 1):
            t_old, v_old = self.data[i]
            t_new, v_new = self.data[i + 1]

            if self._prev_time >= t_new:
                continue
            if time <= t_old:
                break

            time_range = t_new - t_old

            dt1 = max((self._prev_time - t_old) / time_range, 0.0)
            dt2 = min((time - t_old) / time_range, 1.0)

            if self._step is None:
                v1 = interpolate(v_old, v_new, dt1)
                v2 = interpolate(v_old, v_new, dt2)
                value = (dt2 - dt1) * 0.5 * (v1 + v2)
            else:
                dt1 = min(dt1, self._step)
                dt2 = max(self._step, dt2)
                value = (self._step - dt1) * v_old + (dt2 - self._step) * v_new

            if self._per_time:
                value *= time_range.total_seconds() * tools.UNITS.Unit("s")

            sum_value = value if sum_value is None else sum_value + value

        if self._per_time:
            return sum_value.to_reduced_units()

        return sum_value

    def _get_info(self, info):
        if self._per_time:
            up_info = info.copy_with(units=None)
        else:
            up_info = info.copy_with()

        in_info = self.exchange_info(up_info)

        units = tools.UNITS.Unit(in_info.meta.get("units", ""))
        if self._per_time:
            units *= tools.UNITS.Unit("s")
            out_info = in_info.copy_with(units=(1.0 * units).to_reduced_units().units)
        else:
            out_info = in_info.copy_with()

        self._info = out_info
        return out_info
