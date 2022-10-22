"""
Abstract base implementations for components with and without time step.
"""
import collections
import logging
from abc import ABC
from datetime import datetime
from enum import IntEnum
from typing import final

from ..errors import FinamLogError, FinamStatusError
from ..interfaces import (
    ComponentStatus,
    IComponent,
    IInput,
    IOutput,
    ITimeComponent,
    Loggable,
)
from ..tools.connect_helper import ConnectHelper
from ..tools.enum_helper import get_enum_value
from ..tools.log_helper import ErrorLogger, loggable
from .input import Input
from .output import Output


class Component(IComponent, Loggable, ABC):
    """Abstract component implementation."""

    def __init__(self):
        self._status = ComponentStatus.CREATED
        self._inputs = IOList("INPUT")
        self._outputs = IOList("OUTPUT")
        self.base_logger_name = None
        self._connector: ConnectHelper = None

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
        with ErrorLogger(self.logger):
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

    def create_connector(self, pull_data=None):
        """
        Create the component's ConnectHelper

        Parameters
        ----------
        pull_data : arraylike
            Names of the inputs that are to be pulled
        """
        self.logger.debug("create connector")
        self._connector = ConnectHelper(
            self.logger_name,
            self.inputs,
            self.outputs,
            pull_data=pull_data,
        )
        self.inputs.frozen = True
        self.outputs.frozen = True

    def try_connect(
        self, time=None, exchange_infos=None, push_infos=None, push_data=None
    ):
        """Exchange the info and data with linked components.

        Parameters
        ----------
        time : datetime.datatime
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

    def __repr__(self):
        return self.name


class TimeComponent(ITimeComponent, Component, ABC):
    """Abstract component with time step implementation."""

    def __init__(self):
        super().__init__()
        self._time = None

    @property
    def time(self):
        """The component's current simulation time."""
        if not isinstance(self._time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")
        return self._time

    @time.setter
    def time(self, time):
        if not isinstance(time, datetime):
            with ErrorLogger(self.logger):
                raise ValueError("Time must be of type datetime")
        self._time = time


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
