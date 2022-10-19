"""
Implementations of IInput
"""
import logging
from datetime import datetime

from ...data import tools
from ...data.tools import Info
from ...tools.log_helper import LogError
from ..interfaces import FinamMetaDataError, IInput, IOutput, Loggable


class Input(IInput, Loggable):
    """Default input implementation."""

    def __init__(self, name, info=None, **info_kwargs):
        self.source = None
        self.base_logger_name = None
        if name is None:
            raise ValueError("Input: needs a name.")
        self.name = name
        if info_kwargs:
            if info is not None:
                raise ValueError("Input: can't use **kwargs in combination with info")
            info = Info(**info_kwargs)
        self._input_info = info
        self._in_info_exchanged = False

    @property
    def info(self):
        """Info: The input's data info."""
        return self._input_info

    def set_source(self, source):
        """Set the input's source output or adapter

        Parameters
        ----------
        source :
            source output or adapter
        """
        self.logger.debug("set source")

        with LogError(self.logger):
            if self.source is not None:
                raise ValueError(
                    "Source of input is already set! "
                    "(You probably tried to connect multiple outputs to a single input)"
                )
            if not isinstance(source, IOutput):
                raise ValueError("Only IOutput can be set as source for Input")

        self.source = source

    def get_source(self):
        """Get the input's source output or adapter

        Returns
        -------
        Output
            The input's source.
        """
        return self.source

    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime.datatime
            Simulation time of the notification.
        """
        self.logger.debug("source changed")

    def pull_data(self, time):
        """Retrieve the data from the input's source.

        Parameters
        ----------
        time : datetime.datatime
            Simulation time to get the data for.

        Returns
        -------
        array_like
            Data set for the given simulation time.
        """
        self.logger.debug("pull data")
        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")

        data = self.source.get_data(time)

        if "units" in self._input_info.meta:
            data = tools.to_units(data, self._input_info.units)

        with LogError(self.logger):
            tools.check(data, data.name, self._input_info, time, ignore_time=True)

        return data

    def ping(self):
        """Pings upstream to inform outputs about the number of connected inputs.

        Must be called after linking and before the connect phase.
        """
        self.source.pinged()

    def exchange_info(self, info=None):
        """Exchange the data info with the input's source.

        Parameters
        ----------
        info : Info
            request parameters

        Returns
        -------
        dict
            delivered parameters
        """
        self.logger.debug("exchanging info")

        with LogError(self.logger):
            if self._in_info_exchanged:
                raise FinamMetaDataError("Input info was already exchanged.")
            if self._input_info is not None and info is not None:
                raise FinamMetaDataError("An internal info was already provided")
            if self._input_info is None and info is None:
                raise FinamMetaDataError("No metadata provided")
            if info is None:
                info = self._input_info

            if not isinstance(info, Info):
                raise FinamMetaDataError("Metadata must be of type Info")

            in_info = self.source.get_info(info)
            fail_info = {}
            if not info.accepts(in_info, fail_info):
                fail_info = "\n".join(
                    [
                        f"{name} - got {got}, expected {exp}"
                        for name, (got, exp) in fail_info.items()
                    ]
                )
                raise FinamMetaDataError(
                    f"Can't accept incoming data info. Failed entries:\n{fail_info}"
                )

        self._input_info = in_info.copy_with(
            use_none=False, grid=info.grid, **info.meta
        )
        self._in_info_exchanged = True
        return in_info

    @property
    def has_source(self):
        """Flag if this input instance has a source."""
        return self.source is not None

    @property
    def logger_name(self):
        """Logger name derived from base logger name and class name."""
        base_logger = logging.getLogger(self.base_logger_name)
        # logger hierarchy indicated by "." in name
        return ".".join(([base_logger.name, "<-", self.name]))

    @property
    def uses_base_logger_name(self):
        """Whether this class has a 'base_logger_name' attribute."""
        return True


class CallbackInput(Input):
    """Input implementation calling a callback when notified.

    Use for components without time step.

    Parameters
    ----------
    callback : callable
        A callback ``callback(data, time)``, returning the transformed data.
    """

    def __init__(self, callback, name, info=None, **info_kwargs):
        super().__init__(name=name, info=info, **info_kwargs)
        self.callback = callback

    def source_changed(self, time):
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

        self.callback(self, time)
