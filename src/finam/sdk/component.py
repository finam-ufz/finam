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
from ..tools.log_helper import ErrorLogger, is_loggable
from .input import Input
from .output import Output


class Component(IComponent, Loggable, ABC):
    """Abstract component implementation.

    Extend this class for components without time step.
    See :doc:`/finam-book/development/special_components`.
    For components with a time step, use :class:`.TimeComponent`.

    Derived classes overwrite these methods:

    * :meth:`._initialize`
    * :meth:`._connect`
    * :meth:`._validate`
    * :meth:`._update`
    * :meth:`._finalize`
    """

    def __init__(self):
        self._status = ComponentStatus.CREATED
        self._inputs = IOList(self, "INPUT")
        self._outputs = IOList(self, "OUTPUT")
        self.base_logger_name = None
        self._connector: ConnectHelper = None

    @final
    def initialize(self):
        """Initialize the component.

        After the method call, the component's inputs and outputs must be available,
        and the component should have :attr:`.status` :attr:`.ComponentStatus.INITIALIZED`.
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

        After each method call, the component should have :attr:`.status` :attr:`.ComponentStatus.CONNECTED` if
        connecting was completed, :attr:`.ComponentStatus.CONNECTING` if some but not all required initial input(s)
        could be pulled, and :attr:`.ComponentStatus.CONNECTING_IDLE` if nothing could be pulled.
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

        After the method call, the component should have :attr:`.status` :attr:`.ComponentStatus.VALIDATED`.
        """
        self.logger.debug("validate")
        self._validate()
        if self.status != ComponentStatus.FAILED:
            self.status = ComponentStatus.VALIDATED

    def _validate(self):
        """Validate the correctness of the component's settings and coupling.

        Components should overwrite this method.
        """
        self.logger.debug("Method `_validate` not implemented by user.")

    @final
    def update(self):
        """Update the component by one time step.
        Push new values to outputs.

        After the method call, the component should have :attr:`.status`
        :attr:`.ComponentStatus.UPDATED` or :attr:`.ComponentStatus.FINISHED`.
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

        After the method call, the component should have :attr:`.status` :attr:`.ComponentStatus.FINALIZED`.
        """
        self.logger.debug("finalize")
        self._finalize()
        if self.status != ComponentStatus.FAILED:
            self.status = ComponentStatus.FINALIZED

    def _finalize(self):
        """Finalize and clean up the component.

        Components should overwrite this method.
        """
        self.logger.debug("Method `_finalize` not implemented by user.")

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
        """Whether this class has a ``base_logger_name`` attribute. True."""
        return True

    @property
    def connector(self):
        """The component's ConnectHelper"""
        return self._connector

    def create_connector(
        self, pull_data=None, in_info_rules=None, out_info_rules=None, cache=True
    ):
        """Initialize the component's :class:`.tools.ConnectHelper`.

        Parameters
        ----------
        pull_data : arraylike
            Names of the inputs that are to be pulled.
        in_info_rules : dict
            Info transfer rules for inputs.See the examples for details.

            See also :class:`.tools.FromInput`, :class:`.tools.FromOutput` and :class:`.tools.FromValue`.
        out_info_rules : dict
            Info transfer rules for outputs. See the examples for details.

            See also :class:`.tools.FromInput`, :class:`.tools.FromOutput` and :class:`.tools.FromValue`.
        cache : bool
            Whether data and :class:`.Info` objects passed via :meth:`try_connect() <.Component.try_connect>`
            are cached for later calls. Default ``True``.

        .. _examples::

        Examples
        --------

        The following examples show the usage of this method in :meth:`._initialize`.

        .. testsetup:: *

            import finam as fm
            import datetime as dt

            self = fm.modules.CallbackComponent(
                inputs={},
                outputs={},
                callback=lambda inp, _t: {},
                start=dt.datetime(2000, 1, 1),
                step=dt.timedelta(days=1),
            )

        Simple usage if no input data or any metadata from connected components is required:

        .. testcode:: create-connector-simple

            self.inputs.add(name="In", time=self.time, grid=fm.NoGrid())
            self.outputs.add(name="Out", time=self.time, grid=fm.NoGrid())
            self.create_connector()

        To pull specific inputs, use ``pull_data`` like this:

        .. testcode:: create-connector-pull

            self.inputs.add(name="In1", time=self.time, grid=fm.NoGrid())
            self.inputs.add(name="In2", time=self.time, grid=fm.NoGrid())

            self.create_connector(pull_data=["In1", "In2"])

        With the ``in_info_rules`` and ``out_info_rules``, metadata can be transferred between coupling slots.

        Here, the metadata for an output is taken from an input:

        .. testcode:: create-connector-in-to-out

            self.inputs.add(name="In", time=self.time, grid=None, units=None)
            self.outputs.add(name="Out")

            self.create_connector(
                out_info_rules={
                    "Out": [
                        fm.tools.FromInput("In")
                    ]
                }
            )

        The :class:`.Info` object for output ``Out`` will be crated and pushed automatically in :meth:`.try_connect`
        as soon as the metadata for ``In`` becomes available.

        Here, the metadata of an output is composed from the metadata of two inputs and a user-defined value:

        .. testcode:: create-connector-in-to-out-multi

            self.inputs.add(name="In1", time=self.time, grid=None, units=None)
            self.inputs.add(name="In2", time=self.time, grid=None, units=None)
            self.outputs.add(name="Out")

            self.create_connector(
                out_info_rules={
                    "Out": [
                        fm.tools.FromInput("In1", "time", "grid"),
                        fm.tools.FromInput("In2", "units"),
                        fm.tools.FromValue("source", "FINAM"),
                    ]
                }
            )

        The :class:`.Info` object for output ``Out`` would be automatically composed in :meth:`.try_connect`
        as soon as the infos of both inputs become available.
        ``time`` and ``grid`` would be taken from ``In1``, ``units`` from ``In2``,
        and ``source`` would be set to ``"finam"``.

        Rules are evaluated in the given order. Later rules can overwrite attributes set by earlier rules.
        """
        self.logger.debug("create connector")
        self._connector = ConnectHelper(
            self.logger_name,
            self.inputs,
            self.outputs,
            pull_data=pull_data,
            in_info_rules=in_info_rules,
            out_info_rules=out_info_rules,
            cache=cache,
        )
        self.inputs.frozen = True
        self.outputs.frozen = True

    def try_connect(
        self, time=None, exchange_infos=None, push_infos=None, push_data=None
    ):
        """Exchange the info and data with linked components.

        Values passed by the arguments are cached internally for later calls to the method
        if the connector was created with ``cache=True`` (the default).
        Thus, it is sufficient to provide only data and infos that became newly available.
        Giving the same data or infos repeatedly overwrites the cache.

        Sets the component's :attr:`.status` according to success of exchange.

        See :class:`.ConnectHelper` for more details.

        Parameters
        ----------
        time : datetime.datatime
            time for data pulls
        exchange_infos : dict
            currently or newly available input data infos by input name
        push_infos : dict
            currently or newly available output data infos by output name
        push_data : dict
            currently or newly available output data by output name
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

    def __getitem__(self, name):
        """Get an input or output by name. Implements access through square brackets.

        Allows for the use of ``comp["Name"]`` as shortcut for ``comp.inputs["Name"]`` and ``comp.outputs["Name"]``.

        Requires that the name does not appear in inputs as well as outputs.

        Returns
        -------
        IInput or IOutput
            The slot with the given name

        Raises
        ------
        KeyError
            If the name occurs in the inputs as well as the outputs,
            or neither in the inputs nor the outputs.
        """
        if name in self.inputs:
            if name in self.outputs:
                msg = f"Name `{name}` exists in inputs as well as outputs of component {self.name}"
                if self.status == ComponentStatus.CREATED:
                    raise KeyError(msg)

                with ErrorLogger(self.logger):
                    raise KeyError(msg)

            return self.inputs[name]

        if name in self.outputs:
            return self.outputs[name]

        msg = f"Name `{name}` does not exist in inputs or outputs of component `{self.name}`"
        if self.status == ComponentStatus.CREATED:
            msg += " The component is not initialized. Did you miss to add it to the composition?"
            raise KeyError(msg)

        with ErrorLogger(self.logger):
            raise KeyError(msg)

    def __repr__(self):
        return self.name


class TimeComponent(ITimeComponent, Component, ABC):
    """Abstract component with time step implementation.

    Extend this class for components with time step.
    See :doc:`/finam-book/development/components`.
    For components without a time step, use :class:`.Component`.

    Derived classes overwrite these methods

    * :meth:`._initialize`
    * :meth:`._connect`
    * :meth:`._validate`
    * :meth:`._update`
    * :meth:`._finalize`
    """

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
    owner : IComponent
        The owning component of this IOList
    io_type : int, str, IOType
        IO type. Either "INPUT" or "OUTPUT".
    """

    def __init__(self, owner, io_type):
        """
        _summary_

        Parameters
        ----------
        io_type : _type_
            _description_
        """
        self.owner = owner
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
            if (
                is_loggable(item)
                and item.uses_base_logger_name
                and not is_loggable(module)
            ):
                mname = getattr(module, "name", None)
                raise FinamLogError(
                    f"IO: {self.name} '{name}' can't get logger from '{mname}'."
                )
            if is_loggable(item) and item.uses_base_logger_name:
                item.base_logger_name = module.logger_name

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def __getitem__(self, key):
        """Access an item by name."""
        if key in self._dict:
            return self._dict[key]

        if self.owner is None:
            raise KeyError(f"No {self.cls.__name__} `{key}` in unknown component.")

        msg = f"No {self.cls.__name__} `{key}` in component `{self.owner.name}`."
        if self.owner.status == ComponentStatus.CREATED:
            msg += " The component is not initialized. Did you miss to add it to the composition?"
            raise KeyError(msg)

        with ErrorLogger(self.owner.logger):
            raise KeyError(msg)

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
