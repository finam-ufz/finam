"""
Implementations of the coupling interfaces for simpler development of modules and adapters.
"""
import collections
import logging
from abc import ABC
from datetime import datetime
from enum import IntEnum
from typing import final

from ..data import Info, tools
from ..tools.connect_helper import ConnectHelper
from ..tools.enum_helper import get_enum_value
from ..tools.log_helper import LogError, loggable
from .interfaces import (
    ComponentStatus,
    FinamLogError,
    FinamMetaDataError,
    FinamNoDataError,
    FinamStatusError,
    FinamTimeError,
    IAdapter,
    IComponent,
    IInput,
    IOutput,
    ITimeComponent,
    Loggable,
)


class AComponent(IComponent, Loggable, ABC):
    """Abstract component implementation."""

    def __init__(self):
        self._status = None
        self._inputs = IOList("INPUT")
        self._outputs = IOList("OUTPUT")
        self.base_logger_name = None
        self._connector = None

    @final
    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have status INITIALIZED.
        """
        self.logger.debug("init")
        self._initialize()

        self.inputs.frozen = True
        self.outputs.frozen = True

        if self.status != ComponentStatus.FAILED:
            self.status = ComponentStatus.INITIALIZED

    def _initialize(self):
        """Initialize the component.

        Components must overwrite this method.
        After the method call, the component's inputs and outputs must be available.
        """
        raise NotImplementedError(
            f"Method `_initialize` must be implemented by all components, but implementation is missing in {self.name}."
        )

    @final
    def connect(self):
        """Connect exchange data and metadata with linked components.

        The method can be called multiple times if there are failed pull attempts.

        After each method call, the component should have status CONNECTED if
        connecting was completed, CONNECTING if some but not all required initial input(s)
        could be pulled, and `CONNECTING_IDLE` if nothing could be pulled.
        """

        if self.status == ComponentStatus.INITIALIZED:
            self.logger.debug("connect: ping phase")
            for _, inp in self.inputs.items():
                inp.ping()
            self.status = ComponentStatus.CONNECTING
        else:
            self.logger.debug("connect")
            self._connect()

    def _connect(self):
        """Connect exchange data and metadata with linked components.

        Components must overwrite this method.
        """
        raise NotImplementedError(
            f"Method `_connect` must be implemented by all components, but implementation is missing in {self.name}."
        )

    @final
    def validate(self):
        """Validate the correctness of the component's settings and coupling.

        After the method call, the component should have status VALIDATED.
        """
        self.logger.debug("validate")
        self._validate()
        if self.status != ComponentStatus.FAILED:
            self.status = ComponentStatus.VALIDATED

    def _validate(self):
        """Validate the correctness of the component's settings and coupling.

        Components must overwrite this method.
        """
        raise NotImplementedError(
            f"Method `_validate` must be implemented by all components, but implementation is missing in {self.name}."
        )

    @final
    def update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have status UPDATED or FINISHED.
        """
        self.logger.debug("update")
        if isinstance(self, ITimeComponent):
            self.logger.debug("current time: %s", self.time)

        self._update()

        if self.status not in (ComponentStatus.FAILED, ComponentStatus.FINALIZED):
            self.status = ComponentStatus.UPDATED

    def _update(self):
        """Update the component by one time step.
        Push new values to outputs.

        Components must overwrite this method.
        """
        raise NotImplementedError(
            f"Method `_update` must be implemented by all components, but implementation is missing in {self.name}."
        )

    @final
    def finalize(self):
        """Finalize and clean up the component.

        After the method call, the component should have status FINALIZED.
        """
        self.logger.debug("finalize")
        self._finalize()
        if self.status != ComponentStatus.FAILED:
            self.status = ComponentStatus.FINALIZED

    def _finalize(self):
        """Finalize and clean up the component.

        Components must overwrite this method.
        """
        raise NotImplementedError(
            f"Method `_finalize` must be implemented by all components, but implementation is missing in {self.name}."
        )

    @property
    def inputs(self):
        """dict: The component's inputs."""
        return self._inputs

    @property
    def outputs(self):
        """dict: The component's outputs."""
        return self._outputs

    @property
    def status(self):
        """The component's current status."""
        return self._status

    @status.setter
    def status(self, status):
        """The component's current status."""
        with LogError(self.logger):
            self._status = get_enum_value(status, ComponentStatus, FinamStatusError)

    @property
    def name(self):
        """Component name."""
        return self.__class__.__name__

    @property
    def logger_name(self):
        """Logger name derived from base logger name and class name."""
        base_logger = logging.getLogger(self.base_logger_name)
        # logger hierarchy indicated by "." in name
        return ".".join(([base_logger.name, self.name]))

    @property
    def uses_base_logger_name(self):
        """Whether this class has a 'base_logger_name' attribute."""
        return True

    @property
    def connector(self):
        """The component's ConnectHelper"""
        return self._connector

    def create_connector(self, required_in_data=None, required_out_infos=None):
        """
        Create the component's ConnectHelper

        Parameters
        ----------
        required_in_data : arraylike
            Names of the inputs that are to be pulled
        required_out_infos : arraylike
            Names of the outputs that need exchanged info
        """
        self.logger.debug("create connector")
        self._connector = ConnectHelper(
            self.logger_name,
            self.inputs,
            self.outputs,
            required_in_data=required_in_data,
            required_out_infos=required_out_infos,
        )
        self.inputs.frozen = True
        self.outputs.frozen = True

    def try_connect(
        self, time=None, exchange_infos=None, push_infos=None, push_data=None
    ):
        """Exchange the info and data with linked components.

        Parameters
        ----------
        time : datetime
            time for data pulls
        exchange_infos : dict
            currently available input data infos by input name
        push_infos : dict
            currently available output data infos by output name
        push_data : dict
            currently available output data by output name

        Returns
        -------
        ComponentStatus
            the new component status
        """
        self.logger.debug("try connect")

        if self._connector is None:
            raise FinamStatusError(
                f"No connector in component {self.name}. Call `create_connector()` in `_initialize()`."
            )

        self.status = self._connector.connect(
            time,
            exchange_infos=exchange_infos,
            push_infos=push_infos,
            push_data=push_data,
        )
        self.logger.debug("try_connect status is %s", self.status)


class ATimeComponent(ITimeComponent, AComponent, ABC):
    """Abstract component with time step implementation."""

    def __init__(self):
        super().__init__()
        self._time = None

    @property
    def time(self):
        """The component's current simulation time."""
        if not isinstance(self._time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")
        return self._time

    @time.setter
    def time(self, time):
        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")
        self._time = time


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
        # fix to set base-logger for adapters derived from Input source logger
        if isinstance(self, AAdapter):
            if self.uses_base_logger_name and not loggable(source):
                with LogError(self.logger):
                    raise FinamLogError(
                        f"Adapter '{self.name}' can't get base logger from its source."
                    )
            else:
                self.base_logger_name = source.logger_name
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
        time : datetime
            Simulation time of the notification.
        """
        self.logger.debug("source changed")

    def pull_data(self, time):
        """Retrieve the data from the input's source.

        Parameters
        ----------
        time : datetime
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
            tools.check(data, data.name, self._input_info, time)

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
        self.source = None
        self.callback = callback

    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        self.logger.debug("source changed")
        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")

        self.callback(self, time)


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
                raise ValueError("Input: can't use **kwargs in combination with info")
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
        time : datetime
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

        self.data = data
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
        time : datetime
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
        time : datetime
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

        with LogError(self.logger):
            return tools.to_xarray(self.data, self.name, self.info, time)

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
        other : Output
            The adapter or output to add as target to this output.

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


class AAdapter(IAdapter, Input, Output, ABC):
    """Abstract adapter implementation."""

    def __init__(self):
        super().__init__(name=self.__class__.__name__)
        self.source = None
        self.targets = []

    @final
    @property
    def info(self):
        raise NotImplementedError("Property `info` is not implemented for adapters")

    @final
    def push_data(self, data, time):
        """Push data into the output.

        Should notify targets, and can handle the provided date.

        Parameters
        ----------
        data : array_like
            Data set to push.
        time : datetime
            Simulation time of the data set.
        """
        self.logger.debug("push data")
        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")

        self.notify_targets(time)

    @final
    def source_changed(self, time):
        """Informs the input that a new output is available.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """
        self.logger.debug("source changed")
        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise ValueError("Time must be of type datetime")

        self._source_changed(time)

        self.notify_targets(time)

    def _source_changed(self, time):
        """Informs the input that a new output is available.

        Adapters can overwrite this method to handle incoming data.

        Parameters
        ----------
        time : datetime
            Simulation time of the notification.
        """

    @final
    def get_data(self, time):
        self.logger.debug("get data")
        if not isinstance(time, datetime):
            with LogError(self.logger):
                raise FinamTimeError("Time must be of type datetime")

        data = self._get_data(time)
        name = self.get_source().name + "_" + self.name
        return tools.to_xarray(data, name, self._output_info, time)

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
        dict
            delivered parameters
        """
        self.logger.debug("exchanging info")
        with LogError(self.logger):
            if info is None:
                raise FinamMetaDataError("No metadata provided")
            if not isinstance(info, Info):
                raise FinamMetaDataError("Metadata must be of type Info")

        in_info = self.source.get_info(info)

        self._input_info = in_info
        self._output_info = in_info
        return in_info

    @property
    def logger_name(self):
        """Logger name derived from source logger name and class name."""
        base_logger = logging.getLogger(self.base_logger_name)
        return ".".join(([base_logger.name, " >> ", self.name]))


class IOType(IntEnum):
    """IOType of the IOList."""

    INPUT = 0
    OUTPUT = 1


class IOList(collections.abc.Mapping):
    """
    Map for IO.

    Parameters
    ----------
    io_type : int, str, IOType
        IO type. Either "INPUT" or "OUTPUT".
    """

    def __init__(self, io_type):
        """
        _summary_

        Parameters
        ----------
        io_type : _type_
            _description_
        """
        self.type = get_enum_value(io_type, IOType)
        self.cls = [Input, Output][self.type]
        self.name = self.cls.__name__
        self.icls = [IInput, IOutput][self.type]
        self.iname = self.icls.__name__
        self._dict = {}
        self.frozen = False

    def add(self, io=None, *, name=None, info=None, **info_kwargs):
        """
        Add a new IO object either directly ob by attributes.

        Parameters
        ----------
        io : Input or Output, optional
            IO object to add, by default None
        name : str, optional
            Name of the new IO object to add, by default None
        info : Info, optional
            Info of the new IO object to add, by default None
        **info_kwargs
            Optional keyword arguments to instantiate an Info object

        Raises
        ------
        ValueError
            If io is not of the correct type.
        """
        if self.frozen:
            raise ValueError("IO.add: list is frozen.")
        io = self.cls(name, info, **info_kwargs) if io is None else io
        if not isinstance(io, self.icls):
            raise ValueError(f"IO.add: {self.name} is not of type {self.iname}")
        if io.name in self._dict:
            raise ValueError(f"IO.add: {self.name} '{io.name}' already exists.")
        self._dict[io.name] = io

    def set_logger(self, module):
        """
        Set the logger in the items of the IOList.

        Parameters
        ----------
        module : IComponent
            Module holding the IOList.

        Raises
        ------
        FinamLogError
            When item is loggable but not the base module.
        """
        for name, item in self.items():
            if loggable(item) and item.uses_base_logger_name and not loggable(module):
                mname = getattr(module, "name", None)
                raise FinamLogError(
                    f"IO: {self.name} '{name}' can't get logger from '{mname}'."
                )
            if loggable(item) and item.uses_base_logger_name:
                item.base_logger_name = module.logger_name

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        if self.frozen:
            raise ValueError("IO: list is frozen.")
        if key in self._dict:
            raise ValueError(f"IO: {self.name} '{key}' already exists.")
        if not isinstance(value, self.icls):
            raise ValueError(f"IO: {self.name} is not of type {self.iname}")
        if key != value.name:
            raise ValueError(
                f"IO: {self.name} name '{value.name}' differs from key '{key}'"
            )
        self._dict[key] = value

    def __str__(self):
        return str(self._dict)

    def __repr__(self):
        return repr(self._dict)
