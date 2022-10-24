"""
Abstract base implementation for adapters.
"""
import logging
from abc import ABC
from datetime import datetime
from typing import final

from ..data import tools
from ..data.tools import Info
from ..errors import FinamLogError, FinamMetaDataError, FinamTimeError
from ..interfaces import IAdapter, IOutput
from ..tools.log_helper import ErrorLogger, is_loggable
from .input import Input
from .output import Output


class Adapter(IAdapter, Input, Output, ABC):
    """Abstract adapter implementation.

    Extend this class for adapters.
    See :doc:`/finam-book/development/adapters`.

    Simple derived classes overwrite :meth:`._get_data`.

    Adapters that alter the metadata can intercept it in :meth:`._get_info`

    For time-dependent adapters with push-functionality, also overwrite the following:

    * :meth:`._source_updated`
    * :attr:`.needs_push`
    """

    def __init__(self):
        Input.__init__(self, name=self.__class__.__name__)
        Output.__init__(self, name=self.__class__.__name__)
        self.source = None
        self.targets = []

    @final
    @property
    def info(self):
        return self._output_info

    @property
    def needs_pull(self):
        """bool: if the adapter needs pull."""
        return False

    @property
    def needs_push(self):
        """bool: if the adapter needs push."""
        return False

    @final
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
        if not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")

        self.notify_targets(time)

    @final
    def source_updated(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime.datatime
            Simulation time of the notification.
        """
        self.logger.debug("source changed")
        if not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")

        self._source_updated(time)

        self.notify_targets(time)

    def _source_updated(self, time):
        """Informs the input that a new output is available.

        Adapters can overwrite this method to handle incoming data.

        Adapters that make use of this method to accumulate data should also
        overwrite :attr:`.needs_push` to return ``True``.

        Parameters
        ----------
        time : datetime.datatime
            Simulation time of the notification.
        """

    @final
    def get_data(self, time):
        self.logger.debug("get data")
        if not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise FinamTimeError("Time must be of type datetime")

        data = self._get_data(time)
        name = self.get_source().name + "_" + self.name
        return tools.to_xarray(data, name, self._output_info, time, no_time_check=True)

    def _get_data(self, time):
        """Asks the adapter for the transformed data.

        Adapters must overwrite this method.
        """
        raise NotImplementedError(
            f"Method `_get_data` must be implemented by all adapters, but implementation is missing in {self.name}."
        )

    @final
    def get_info(self, info):
        """Exchange and get the output's data info.

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
        self._output_info = self._get_info(info)
        return self._output_info

    def _get_info(self, info):
        """Exchange and get the output's data info.

        Adapters can overwrite this method to manipulate the metadata for the output.

        Parameters
        ----------
        info : Info
            Requested data info

        Returns
        -------
        dict
            Delivered data info
        """
        return self.exchange_info(info)

    def pinged(self):
        """Called when receiving a ping from a downstream input."""
        self.ping()

    @final
    def exchange_info(self, info=None):
        """Exchange the data info with the input's source.

        Parameters
        ----------
        info : Info
            request parameters

        Returns
        -------
        Info
            delivered parameters
        """
        self.logger.debug("exchanging info")
        with ErrorLogger(self.logger):
            if info is None:
                raise FinamMetaDataError("No metadata provided")
            if not isinstance(info, Info):
                raise FinamMetaDataError("Metadata must be of type Info")

        in_info = self.source.get_info(info)

        self._input_info = in_info
        self._output_info = in_info
        return in_info

    def set_source(self, source):
        """Set the adapter input's source output or adapter

        Parameters
        ----------
        source :
            source output or adapter
        """
        self.logger.debug("set source")
        # fix to set base-logger for adapters derived from Input source logger
        if self.uses_base_logger_name and not is_loggable(source):
            with ErrorLogger(self.logger):
                raise FinamLogError(
                    f"Adapter '{self.name}' can't get base logger from its source."
                )
        else:
            self.base_logger_name = source.logger_name

        with ErrorLogger(self.logger):
            if self.source is not None:
                raise ValueError(
                    "Source of input is already set! "
                    "(You probably tried to connect multiple outputs to a single input)"
                )
            if not isinstance(source, IOutput):
                raise ValueError("Only IOutput can be set as source for Input")

        self.source = source

    @property
    def logger_name(self):
        """Logger name derived from source logger name and class name."""
        base_logger = logging.getLogger(self.base_logger_name)
        return ".".join(([base_logger.name, " >> ", self.name]))
