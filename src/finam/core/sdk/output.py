"""
Implementations of IOutput
"""
import logging
from datetime import datetime

from ...data import tools
from ...data.tools import Info
from ...tools.log_helper import LogError
from ..interfaces import FinamMetaDataError, FinamNoDataError, IInput, IOutput, Loggable


class Output(IOutput, Loggable):
    """Default output implementation."""

    def __init__(self, name=None, info=None, **info_kwargs):
        self.targets = []
        self.data = None
        self._output_info = None
        self.base_logger_name = None
        if name is None:
            raise ValueError("Output: needs a name.")
        self.name = name

        if info_kwargs:
            if info is not None:
                raise ValueError("Output: can't use **kwargs in combination with info")
            info = Info(**info_kwargs)
        if info is not None:
            self.push_info(info)

        self._connected_inputs = 0
        self._out_infos_exchanged = 0

    @property
    def info(self):
        """Info: The input's data info."""
        if self._output_info is None:
            raise FinamNoDataError("No data info available")
        if self.has_targets and self._out_infos_exchanged < self._connected_inputs:
            raise FinamNoDataError("Data info was not completely exchanged yet")

        return self._output_info

    def has_info(self):
        """Returns if the output has a data info.

        The info is not required to be validly exchanged.
        """
        return self._output_info is not None

    @property
    def is_push_based(self):
        """Returns if the output is push-based, and requires push as startup."""
        return True

    def add_target(self, target):
        """Add a target input or adapter for this output.

        Parameters
        ----------
        target : Input
            The target to add.
        """
        self.logger.debug("add target")
        if not isinstance(target, IInput):
            with LogError(self.logger):
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

    def pinged(self):
        """Called when receiving a ping from a downstream input."""
        self._connected_inputs += 1

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

        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")

        if self.has_targets and self._out_infos_exchanged < self._connected_inputs:
            raise FinamNoDataError("Can't push data before output info was exchanged.")

        self.data = tools.to_xarray(data, self.name, self.info, time)
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
            with LogError(self.logger):
                raise FinamMetaDataError("Metadata must be of type Info")
        self._output_info = info

    def notify_targets(self, time):
        """Notify all targets by calling their ``source_changed(time)`` method.

        Parameters
        ----------
        time : datetime.datatime
            Simulation time of the simulation.
        """
        self.logger.debug("notify targets")
        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")

        for target in self.targets:
            target.source_changed(time)

    def get_data(self, time):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : datetime.datatime
            simulation time to get the data for.

        Returns
        -------
        any
            data-set for the requested time.
            Should return `None` if no data is available.
        """
        self.logger.debug("get data")
        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")

        if self._output_info is None:
            raise FinamNoDataError(f"No data info available in {self.name}")
        if self._out_infos_exchanged < self._connected_inputs:
            raise FinamNoDataError(f"Data info was not yet exchanged in {self.name}")
        if self.data is None:
            raise FinamNoDataError(f"No data available in {self.name}")

        return self.data

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

        if self._output_info.grid is None:
            if info.grid is None:
                raise FinamMetaDataError(
                    "Can't set property `grid` from target info, as it is not provided"
                )

            self._output_info.grid = info.grid

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
        """Whether this class has a 'base_logger_name' attribute."""
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
    def is_push_based(self):
        """Returns if the output is push-based, and requires push as startup."""
        return False

    def push_data(self, data, time):
        raise NotImplementedError("CallbackInput does not support push of data")

    def get_data(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime.datatime
            Simulation time of the notification.
        """
        self.logger.debug("source changed")
        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")

        if self._output_info is None:
            raise FinamNoDataError(f"No data info available in {self.name}")
        if self._out_infos_exchanged < self._connected_inputs:
            raise FinamNoDataError(f"Data info was not yet exchanged in {self.name}")

        data = self.callback(self, time)

        if data is None:
            raise FinamNoDataError(f"No data available in {self.name}")

        return tools.to_xarray(data, self.name, self.info, time)
