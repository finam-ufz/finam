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
from ..interfaces import IAdapter, IOutput, ITimeDelayAdapter
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
        self._name = self.__class__.__name__
        self._source = None
        self._targets = []

    def with_name(self, name):
        """Renames the adapter and returns self."""
        self._name = name
        return self

    @property
    def time(self):
        """The output's time of the latest available data"""
        return None

    @property
    def is_static(self):
        return False

    @final
    @property
    def info(self):
        return self._output_info

    @final
    @property
    def in_info(self):
        """Info from connected source."""
        return self._input_info

    @property
    def needs_pull(self):
        """bool: if the adapter needs pull."""
        return False

    @property
    def needs_push(self):
        """bool: if the adapter needs push."""
        return False

    @property
    def metadata(self):
        """
        The adapter's metadata.
        Will only be called after the connect phase from :attr:`Composition.metadata`.

        Adapters can overwrite this property to add their own specific metadata:

        .. testcode:: metadata

            import finam as fm

            class MyAdapter(fm.Adapter):

                @property
                def metadata(self):
                    # Get the default metadata
                    md = super().metadata

                    # Add your own metadata
                    md["my_field"] = "some value"

                    # Return the dictionary
                    return md

        .. testcode:: metadata
            :hide:

            ada = MyAdapter()


        Returns
        -------
        dict
            A ``dict`` with the following default metadata:
              - ``name`` - the component's name
              - ``class`` - the component's class
        """
        meta = {
            "name": self.name,
            "class": self.__class__.__module__ + "." + self.__class__.__qualname__,
            "out_info": self._output_info.as_dict(),
        }

        if self._input_info is not None:
            meta["in_info"] = self._input_info.as_dict()

        return meta

    @final
    def push_data(self, data, time):
        """Push data into the output.

        Should notify targets, and can handle the provided date.

        Parameters
        ----------
        data : array_like
            Data set to push.
        time : :class:`datetime <datetime.datetime>`
            Simulation time of the data set.
        """
        self.logger.debug("push data")
        if time is not None and not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")

        self.notify_targets(time)

    @final
    def source_updated(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time of the notification.
        """
        self.logger.debug("source updated")
        if time is not None and not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")

        self._source_updated(time)

        self.notify_targets(time)

    def notify_targets(self, time):
        """Notify all targets by calling their ``source_updated(time)`` method.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time of the simulation.
        """
        self.logger.trace("notify targets")
        if time is not None and not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")

        for target in self.targets:
            target.source_updated(time)

    def _source_updated(self, time):
        """Informs the input that a new output is available.

        Adapters can overwrite this method to handle incoming data.

        Adapters that make use of this method to accumulate data should also
        overwrite :attr:`.needs_push` to return ``True``.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time of the notification.
        """

    def get_data(self, time, target):
        """Get the transformed data of this adapter.

        Internally calls :meth:`._get_data`.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time to get the data for.
        target : :class:`.IInput`
            Requesting end point of this pull.

        Returns
        -------
        :class:`pint.Quantity`
            Transformed data-set for the requested time.
        """
        self.logger.debug("get data")
        if time is not None and not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise FinamTimeError("Time must be of type datetime")

        data = self._get_data(time, target)

        with ErrorLogger(self.logger):
            xdata, conv = tools.prepare(data, self._output_info, report_conversion=True)
            if conv is not None:
                self.logger.profile(
                    "converted units from %s to %s (%d entries)", *conv, xdata.size
                )
            return xdata

    def _get_data(self, time, target):
        """Get the transformed data of this adapter.

        Adapters must overwrite this method.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time to get the data for.
        target : :class:`.IInput`
            Requesting end point of this pull.

        Returns
        -------
        :class:`pint.Quantity`
            Transformed data-set for the requested time.
        """
        raise NotImplementedError(
            f"Method `_get_data` must be implemented by all adapters, but implementation is missing in {self.name}."
        )

    def get_info(self, info):
        """Exchange and get the output's data info.

        Parameters
        ----------
        info : :class:`.Info`
            Requested data info

        Returns
        -------
        Info
            Delivered data info

        Raises
        ------
        FinamNoDataError
            Raises the error if no info is available
        """
        self.logger.trace("get info")
        self._output_info = self._get_info(info)
        return self._output_info

    def _get_info(self, info):
        """Exchange and get the output's data info.

        Adapters can overwrite this method to manipulate the metadata for the output.

        Parameters
        ----------
        info : :class:`.Info`
            Requested data info

        Returns
        -------
        Info
            Delivered data info
        """
        return self.exchange_info(info)

    def pinged(self, source):
        """Called when receiving a ping from a downstream input."""
        self._source.pinged(self if self.needs_push else source)

    @final
    def exchange_info(self, info=None):
        """Exchange the data info with the input's source.

        Parameters
        ----------
        info : :class:`.Info`
            request parameters

        Returns
        -------
        Info
            delivered parameters
        """
        self.logger.trace("exchanging info")
        with ErrorLogger(self.logger):
            if info is None:
                raise FinamMetaDataError("No metadata provided")
            if not isinstance(info, Info):
                raise FinamMetaDataError("Metadata must be of type Info")

        in_info = self._source.get_info(info)

        self._input_info = in_info
        self._output_info = in_info
        return in_info

    @property
    def source(self):
        """Get the input's source output or adapter

        Returns
        -------
        :class:`.IOutput`
            The input's source.
        """
        return super().source

    @source.setter
    def source(self, source):
        """Set the adapter input's source output or adapter

        Parameters
        ----------
        source :
            source output or adapter
        """
        self.logger.trace("set source")
        # fix to set base-logger for adapters derived from Input source logger
        if self.uses_base_logger_name and not is_loggable(source):
            with ErrorLogger(self.logger):
                raise FinamLogError(
                    f"Adapter '{self.name}' can't get base logger from its source."
                )
        else:
            self.base_logger_name = source.logger_name

        with ErrorLogger(self.logger):
            if self._source is not None:
                raise ValueError(
                    "Source of input is already set! "
                    "(You probably tried to connect multiple outputs to a single input)"
                )
            if not isinstance(source, IOutput):
                raise ValueError("Only IOutput can be set as source for Input")

        self._source = source

    @property
    def logger_name(self):
        """Logger name derived from source logger name and class name."""
        base_logger = logging.getLogger(self.base_logger_name)
        return ".".join(([base_logger.name, " >> ", self.name]))

    def finalize(self):
        """Called at the end of each run. Calls :meth:`._finalize`."""
        self.logger.debug("finalize")
        self._finalize()

    def _finalize(self):
        """Called at the end of each run. Overwrite this for cleanup."""


class TimeDelayAdapter(Adapter, ITimeDelayAdapter, ABC):
    """Base class for adapters that delay/offset time to resolve dependency cycles."""

    def __init__(self):
        super().__init__()
        self.initial_time = None

    def get_data(self, time, target):
        """Get the transformed data of this adapter.

        Internally calls :meth:`._get_data`.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            Simulation time to get the data for.
        target : :class:`.IInput`
            Requesting end point of this pull.

        Returns
        -------
        :class:`pint.Quantity`
            Transformed data-set for the requested time.
        """
        self.logger.debug("get data")
        if time is not None and not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise FinamTimeError("Time must be of type datetime")

        new_time = self.with_delay(time)
        data = self._get_data(new_time, target)

        self._pulled(time)

        with ErrorLogger(self.logger):
            xdata, conv = tools.prepare(data, self._output_info, report_conversion=True)
            if conv is not None:
                self.logger.profile(
                    "converted units from %s to %s (%d entries)", *conv, xdata.size
                )
            return xdata

    def _get_data(self, time, target):
        """Get the output's data-set for the given time.

        Parameters
        ----------
        time : :class:`datetime <datetime.datetime>`
            simulation time to get the data for.

        Returns
        -------
        array_like
            data-set for the requested time.
        """
        d = self.pull_data(time, target)
        return d

    def _pulled(self, time):
        """This method is called during pulls, with the original pull time.

        Can be overwritten to store the original pull time,
        as in :meth:`._get_data()` only the manipulated time is available.

        Called after :meth:`._get_data()` (i.e. after the actual pull).

        Parameters
        ----------

        time : :class:`datetime <datetime.datetime>`
            The original (requested) time of the current pull.
        """

    def get_info(self, info):
        """Exchange and get the output's data info.

        Parameters
        ----------
        info : :class:`.Info`
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
        self.logger.trace("get info")
        self._output_info = self._get_info(info)
        self.initial_time = self._output_info.time
        return self._output_info
