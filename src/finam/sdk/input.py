"""
Implementations of IInput
"""
import logging
from datetime import datetime

from ..data import tools
from ..data.tools import Info
from ..errors import FinamMetaDataError
from ..interfaces import IInput, IOutput, Loggable
from ..tools.log_helper import ErrorLogger


class Input(IInput, Loggable):
    """Default input implementation."""

    def __init__(self, name, info=None, static=False, **info_kwargs):
        Loggable.__init__(self)
        self._source = None
        self.base_logger_name = None
        if name is None:
            raise ValueError("Input: needs a name.")
        self._name = name
        self._static = static
        if info_kwargs:
            if info is not None:
                raise ValueError("Input: can't use **kwargs in combination with info")
            info = Info(**info_kwargs)
        self._input_info = info
        self._in_info_exchanged = False
        self._cached_data = None
        self._transform = None

    @property
    def name(self):
        """Input name."""
        return self._name

    @property
    def is_static(self):
        return self._static

    @property
    def info(self):
        """Info: The input's data info."""
        return self._input_info

    @property
    def needs_pull(self):
        """bool: if the input needs pull."""
        return True

    @property
    def needs_push(self):
        """bool: if the input needs push."""
        return False

    @property
    def source(self):
        """Get the input's source output or adapter

        Returns
        -------
        :class:`.IOutput`
            The input's source.
        """
        return self._source

    @source.setter
    def source(self, source):
        """Set the input's source output or adapter

        Parameters
        ----------
        source : :class:`.IOutput`
            source output or adapter
        """
        self.logger.trace("set source")

        with ErrorLogger(self.logger):
            if self._source is not None:
                raise ValueError(
                    "Source of input is already set! "
                    "(You probably tried to connect multiple outputs to a single input)"
                )
            if not isinstance(source, IOutput):
                raise ValueError("Only IOutput can be set as source for Input")

        self._source = source

    def source_updated(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time of the notification.
        """
        self.logger.trace("source changed")

    def pull_data(self, time, target=None):
        """Retrieve the data from the input's source.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time to get the data for.
        target : :class:`.IInput` or None
            Requesting end point of this pull.
            Should be ``None`` for normal input pulls in components.
            Simple adapters should forward the source in :meth:`.Adapter._get_data`.
            Push-based adapters should use ``self`` in :meth:`.Adapter._source_updated`.

        Returns
        -------
        :class:`pint.Quantity`
            Data set for the given simulation time.
        """
        self.logger.trace("pull data")

        if time is not None and not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")

        if self.is_static:
            if self._cached_data is None:
                data = self._source.get_data(time, target or self)
                with ErrorLogger(self.logger):
                    self._cached_data = self._convert_and_check(data)
            data = self._cached_data
        else:
            data = self._source.get_data(time, target or self)
            with ErrorLogger(self.logger):
                data = self._convert_and_check(data)

        return data

    def _convert_and_check(self, data):
        # transform compatible data between grids
        if self._transform is not None:
            with ErrorLogger(self.logger):
                data = self._transform(data)
            self.logger.profile(
                "converted data between compatible grids (%d entries)", data.size
            )

        # convert units
        data, conv = tools.to_units(
            data, self._input_info.units, check_equivalent=True, report_conversion=True
        )
        if conv is not None:
            self.logger.profile(
                "converted units from %s to %s (%d entries)", *conv, data.size
            )
        tools.check(data, self._input_info)
        return data

    def ping(self):
        """Pings upstream to inform outputs about the number of connected inputs.

        Must be called after linking and before the connect phase.
        """
        self._source.pinged(self)

    def exchange_info(self, info=None):
        """Exchange the data info with the input's source.

        Parameters
        ----------
        info : :class:`.Info`
            request parameters

        Returns
        -------
        dict
            delivered parameters
        """
        self.logger.trace("exchanging info")

        with ErrorLogger(self.logger):
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

        src_info = self._source.get_info(info)

        with ErrorLogger(self.logger):
            fail_info = {}
            if not info.accepts(src_info, fail_info):
                fail_info = "\n".join(
                    [
                        f"{name} - got {got}, expected {exp}"
                        for name, (got, exp) in fail_info.items()
                    ]
                )
                raise FinamMetaDataError(
                    f"Can't accept incoming data info. Failed entries:\n{fail_info}"
                )

        self._input_info = src_info.copy_with(
            use_none=False, time=info.time, grid=info.grid, **info.meta
        )
        self._in_info_exchanged = True
        with ErrorLogger(self.logger):
            self._transform = src_info.grid.get_transform_to(self._input_info.grid)

        # pylint: disable-next=fixme
        # TODO: check if this is correct (was src_info before)
        return self._input_info

    @property
    def has_source(self):
        """Flag if this input instance has a source."""
        return self._source is not None

    @property
    def logger_name(self):
        """Logger name derived from base logger name and class name."""
        base_logger = logging.getLogger(self.base_logger_name)
        # logger hierarchy indicated by "." in name
        return ".".join(([base_logger.name, "<-", self.name]))

    @property
    def uses_base_logger_name(self):
        """Whether this class has a ``base_logger_name`` attribute. True."""
        return True


class CallbackInput(Input):
    """Input implementation calling a callback when notified.

    Use for components without time step.

    Parameters
    ----------
    callback : callable
        A callback ``callback(caller, time)``, returning the transformed data.
    """

    def __init__(self, callback, name, info=None, static=False, **info_kwargs):
        super().__init__(name=name, info=info, static=static, **info_kwargs)
        self.callback = callback

    @property
    def needs_pull(self):
        """bool: if the input needs pull."""
        return False

    @property
    def needs_push(self):
        """bool: if the input needs push."""
        return True

    def source_updated(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time of the notification.
        """
        self.logger.trace("source changed")
        if time is not None and not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")

        self.callback(self, time)
