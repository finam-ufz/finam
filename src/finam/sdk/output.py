"""
Implementations of IOutput
"""
import logging
from datetime import datetime

from ..data import tools
from ..data.tools import Info
from ..errors import (
    FinamDataError,
    FinamMetaDataError,
    FinamNoDataError,
    FinamTimeError,
)
from ..interfaces import IAdapter, IInput, IOutput, Loggable
from ..tools.log_helper import ErrorLogger


class Output(IOutput, Loggable):
    """Default output implementation."""

    def __init__(self, name=None, info=None, static=False, **info_kwargs):
        self.targets = []
        self.data = []
        self._output_info = None
        self.base_logger_name = None
        if name is None:
            raise ValueError("Output: needs a name.")
        self.name = name
        self._static = static

        if info_kwargs:
            if info is not None:
                raise ValueError("Output: can't use **kwargs in combination with info")
            info = Info(**info_kwargs)
        if info is not None:
            self.push_info(info)

        self._connected_inputs = {}
        self._out_infos_exchanged = 0

    @property
    def is_static(self):
        return self._static

    @property
    def info(self):
        """Info: The input's data info."""
        if self._output_info is None:
            raise FinamNoDataError("No data info available")
        if self.has_targets and self._out_infos_exchanged < len(self._connected_inputs):
            raise FinamNoDataError("Data info was not completely exchanged yet")

        return self._output_info

    @property
    def needs_pull(self):
        """bool: if the output needs pull."""
        return False

    @property
    def needs_push(self):
        """bool: if the output needs push."""
        return True

    def has_info(self):
        """Returns if the output has a data info.

        The info is not required to be validly exchanged.
        """
        return self._output_info is not None

    def add_target(self, target):
        """Add a target input or adapter for this output.

        Parameters
        ----------
        target : Input
            The target to add.
        """
        self.logger.debug("add target")
        if not isinstance(target, IInput):
            with ErrorLogger(self.logger):
                raise ValueError("Only IInput can added as target for IOutput")

        self.targets.append(target)

    def get_targets(self):
        """Get target inputs and adapters for this output.

        Returns
        -------
        list
            List of targets.
        """
        return self.targets

    def pinged(self, source):
        """Called when receiving a ping from a downstream input."""
        if not isinstance(source, IAdapter) and source in self._connected_inputs:
            with ErrorLogger(self.logger):
                raise ValueError(
                    f"Input '{source.name}' is already connected to this output"
                )
        self._connected_inputs[source] = None

    def push_data(self, data, time):
        """Push data into the output.

        Should notify targets, and can handle the provided date.

        Parameters
        ----------
        data : array_like
            Data set to push.
        time : datetime.datatime
            Simulation time of the data set.
        """
        self.logger.debug("push data")

        if not self.has_targets:
            self.logger.debug("skipping push to unconnected output")
            return

        if not self.is_static and not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")

        if self.has_targets and self._out_infos_exchanged < len(self._connected_inputs):
            raise FinamNoDataError("Can't push data before output info was exchanged.")

        if self.is_static and len(self.data) > 0:
            raise FinamDataError("Can't push data repeatedly to a static output.")

        with ErrorLogger(self.logger):
            self.data.append((time, tools.to_xarray(data, self.name, self.info, time)))

        self.logger.debug("data cache: %d", len(self.data))

        self.notify_targets(time)

    def push_info(self, info):
        """Push data info into the output.

        Parameters
        ----------
        info : Info
            Delivered data info
        """
        self.logger.debug("push info")
        if not isinstance(info, Info):
            with ErrorLogger(self.logger):
                raise FinamMetaDataError("Metadata must be of type Info")
        self._output_info = info

    def notify_targets(self, time):
        """Notify all targets by calling their ``source_updated(time)`` method.

        Parameters
        ----------
        time : datetime.datatime
            Simulation time of the simulation.
        """
        self.logger.debug("notify targets")
        if not self.is_static and not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")

        for target in self.targets:
            target.source_updated(time)

    def get_data(self, time, target):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : datetime.datatime
            simulation time to get the data for.
        target : IInput or None
            Requesting end point of this pull.

        Returns
        -------
        :class:`xarray.DataArray`
            data-set for the requested time.

        Raises
        ------
        FinamNoDataError
            Raises the error if no data is available
        """
        self.logger.debug("get data")
        if not self.is_static and not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")

        if self._output_info is None:
            raise FinamNoDataError(f"No data info available in {self.name}")
        if self._out_infos_exchanged < len(self._connected_inputs):
            raise FinamNoDataError(f"Data info was not yet exchanged in {self.name}")
        if len(self.data) == 0:
            raise FinamNoDataError(f"No data available in {self.name}")

        data = self.data[0][1] if self.is_static else self._interpolate(time)

        if not self.is_static:
            data_count = len(self.data)
            self._clear_data(time, target)

            if len(self.data) < data_count:
                self.logger.debug(
                    "reduced data cache: %d -> %d", data_count, len(self.data)
                )

        return data

    def _clear_data(self, time, target):
        self._connected_inputs[target] = time
        if any(t is None for t in self._connected_inputs.values()):
            return

        t_min = min(self._connected_inputs.values())
        while len(self.data) > 1 and self.data[1][0] <= t_min:
            self.data.pop(0)

    def _interpolate(self, time):
        if time < self.data[0][0] or time > self.data[-1][0]:
            raise FinamTimeError(
                f"Requested time {time} out of range [{self.data[0][0]}, {self.data[-1][0]}]"
            )
        for i, (t, data) in enumerate(self.data):
            if time > t:
                continue
            if time == t:
                return data

            t_prev, data_prev = self.data[i - 1]
            diff = t - t_prev
            t_half = t_prev + diff / 2

            if time < t_half:
                return data_prev

            return data

        raise FinamTimeError(
            f"Time interpolation failed. This should not happen and is probably a bug. "
            f"Time is {time}."
        )

    def get_info(self, info):
        """Exchange and get the output's data info.

        For internal use. To get the info in a component, use property `info`.

        Parameters
        ----------
        info : Info
            Requested data info

        Returns
        -------
        dict
            Delivered data info

        Raises
        ------
        FinamNoDataError
            Raises the error if no info is available
        """
        self.logger.debug("get info")

        if self._output_info is None:
            raise FinamNoDataError("No data info available")

        if self._out_infos_exchanged > 0:
            fail_info = {}
            if not self._output_info.accepts(info, fail_info, ignore_none=True):
                fail_info = "\n".join(
                    [
                        f"{name} - got {got}, expected {exp}"
                        for name, (got, exp) in fail_info.items()
                    ]
                )
                with ErrorLogger(self.logger):
                    raise FinamMetaDataError(
                        f"Can't accept multiple conflicting data infos. Failed entries:\n{fail_info}"
                    )

        with ErrorLogger(self.logger):
            if self._output_info.grid is None:
                if info.grid is None:
                    raise FinamMetaDataError(
                        "Can't set property `grid` from target info, as it is not provided"
                    )

                self._output_info.grid = info.grid

            if self._output_info.time is None:
                if not self.is_static and info.time is None:
                    raise FinamMetaDataError(
                        "Can't set property `time` from target info, as it is not provided"
                    )

                self._output_info.time = info.time

            for k, v in self._output_info.meta.items():
                if v is None:
                    if k not in info.meta or info.meta[k] is None:
                        raise FinamMetaDataError(
                            f"Can't set property `meta.{k}` from target info, as it is not provided"
                        )

                    self._output_info.meta[k] = info.meta[k]

        self._out_infos_exchanged += 1

        return self._output_info

    def chain(self, other):
        """Chain outputs and adapters.

        Parameters
        ----------
        other : Input
            The adapter or input to add as target to this output.

        Returns
        -------
        Output
            The last element of the chain.
        """
        self.logger.debug("chain")
        self.add_target(other)
        other.set_source(self)
        return other

    @property
    def has_targets(self):
        """Flag if this output instance has any targets."""
        return bool(self.targets)

    @property
    def logger_name(self):
        """Logger name derived from base logger name and class name."""
        base_logger = logging.getLogger(self.base_logger_name)
        # logger hierarchy indicated by "." in name
        return ".".join(([base_logger.name, "->", self.name]))

    @property
    def uses_base_logger_name(self):
        """Whether this class has a ``base_logger_name`` attribute. True."""
        return True


class CallbackOutput(Output):
    """Output implementation calling a callback when pulled.

    Use for components without time step.

    Parameters
    ----------
    callback : callable
        A callback ``callback(data, time)``, returning the transformed data.
    """

    def __init__(self, callback, name, info=None, **info_kwargs):
        super().__init__(name=name, info=info, **info_kwargs)
        self.callback = callback

    @property
    def is_static(self):
        return False

    @property
    def needs_push(self):
        """bool: if the output needs push."""
        return False

    @property
    def needs_pull(self):
        """bool: if the output needs pull."""
        return True

    def push_data(self, data, time):
        raise NotImplementedError("CallbackInput does not support push of data")

    def get_data(self, time, target):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : datetime.datatime
            Simulation time to get the data for.
        target : IInput
            Requesting end point of this pull

        Returns
        -------
        :class:`xarray.DataArray`
            Data-set for the requested time.

        Raises
        ------
        FinamNoDataError
            Raises the error if no data is available
        """
        self.logger.debug("source changed")
        if not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")

        if self._output_info is None:
            raise FinamNoDataError(f"No data info available in {self.name}")
        if self._out_infos_exchanged < len(self._connected_inputs):
            raise FinamNoDataError(f"Data info was not yet exchanged in {self.name}")

        data = self.callback(self, time)

        if data is None:
            raise FinamNoDataError(f"No data available in {self.name}")

        with ErrorLogger(self.logger):
            return tools.to_xarray(data, self.name, self.info, time)
