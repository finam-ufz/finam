"""Iterative connection helpers."""
import copy
import logging
from abc import ABC

from finam.interfaces import ComponentStatus, Loggable

from ..data.tools import Info
from ..errors import FinamNoDataError, FinamTimeError
from ..tools.log_helper import ErrorLogger


class MissingInfoError(Exception):
    """Internal error type for handling missing infos for transfer rules"""


class InfoSource(ABC):
    """Base class for info transfer rules from inputs or outputs"""

    def __init__(self, name, fields):
        self.name = name

        if fields is not None and not isinstance(fields, list):
            raise TypeError(
                "Fields must be a list of metadata attributes as strings, or None."
            )

        self.fields = fields or []


class FromInput(InfoSource):
    """Info transfer rule from an input.

    See :meth:`.Component.create_connector` for usage details.

    Parameters
    ----------
    name : str
        Name of the input to take info from
    fields : list of str, optional
        Info fields to take from the input.
        Takes all fields if this is empty.
    """

    def __init__(self, name, fields=None):
        super().__init__(name, fields)


class FromOutput(InfoSource):
    """Info transfer rule from an output.

    See :meth:`.Component.create_connector` for usage details.

    Parameters
    ----------
    name : str
        Name of the output to take info from
    fields : list of str, optional
        Info fields to take from the output.
        Takes all fields if this is empty.
    """

    def __init__(self, name, fields=None):
        super().__init__(name, fields)


class FromValue:
    """
    Info transfer rule from a given value

    Parameters
    ----------
    field : str
        Field to set.
    value : any
        Value to set.
    """

    def __init__(self, field, value):
        self.field = field
        self.value = value


class ConnectHelper(Loggable):
    """Helper for iterative connect.

    Warning:
        This class is not intended for direct use!
        Use :meth:`.Component.create_connector` and :meth:`.Component.try_connect` instead.

    Parameters
    ----------
    logger : Logger
        Logger to use
    inputs : dict
        All inputs of the component.
    outputs : dict
        All outputs of the component.
    in_info_rules : dict
        Info transfer rules for inputs.
    out_info_rules : dict
        Info transfer rules for outputs.
    pull_data : arraylike
        Names of the inputs that are to be pulled.
    cache : bool
        Whether data and :class:`.Info` objects passed via :meth:`connect() <.ConnectHelper.connect>`
        are cached for later calls. Default ``True``.
    """

    def __init__(
        self,
        logger_name,
        inputs,
        outputs,
        pull_data=None,
        in_info_rules=None,
        out_info_rules=None,
        cache=True,
    ):
        super().__init__()

        self.base_logger_name = logger_name
        self._inputs = inputs
        self._outputs = outputs
        self._cache = cache

        with ErrorLogger(self.logger):
            for name in pull_data or []:
                if name not in self._inputs:
                    raise KeyError(
                        f"No input named '{name}' available to get info for."
                    )

        self._exchanged_in_infos = {name: None for name in self.inputs.keys()}
        self._exchanged_out_infos = {name: None for name in self.outputs.keys()}

        self._pulled_data = {name: None for name in pull_data or []}

        self._pushed_infos = {
            name: out.has_info() for name, out in self.outputs.items()
        }
        self._pushed_data = {
            name: False for name, out in self.outputs.items() if out.needs_push
        }

        self._in_info_rules = in_info_rules or {}
        self._out_info_rules = out_info_rules or {}

        with ErrorLogger(self.logger):
            self._check_info_rules()

        self._in_info_cache = {}
        self._out_info_cache = {}
        self._out_data_cache = {}

    def add_in_info_rule(self, in_name, rule):
        """
        Add an input info rule.

        Parameters
        ----------
        in_name : str
            Name of the input to add an info rule to.
        rule : FromOutput or FromInput or FromValue
            Rule to add.
        """
        if in_name in self._in_info_rules:
            self._in_info_rules[in_name].append(rule)
        else:
            self._in_info_rules[in_name] = [rule]
        with ErrorLogger(self.logger):
            self._check_info_rules()

    def add_out_info_rule(self, out_name, rule):
        """
        Add an output info rule.

        Parameters
        ----------
        out_name : str
            Name of the output to add an info rule to.
        rule : FromInput or FromOutput or FromValue
            Rule to add.
        """
        if out_name in self._out_info_rules:
            self._out_info_rules[out_name].append(rule)
        else:
            self._out_info_rules[out_name] = [rule]
        with ErrorLogger(self.logger):
            self._check_info_rules()

    def _apply_rules(self, rules):
        info = Info(time=None, grid=None)
        for rule in rules:
            if isinstance(rule, FromInput):
                in_info = self.in_infos[rule.name]
                if in_info is None:
                    raise MissingInfoError()
                _transfer_fields(in_info, info, rule.fields)
            elif isinstance(rule, FromOutput):
                out_info = self.out_infos[rule.name]
                if out_info is None:
                    raise MissingInfoError()
                _transfer_fields(out_info, info, rule.fields)
            elif isinstance(rule, FromValue):
                if rule.field == "time":
                    info.time = rule.value
                elif rule.field == "grid":
                    info.grid = rule.value
                else:
                    info.meta[rule.field] = rule.value

        return info

    def _check_info_rules(self):
        for name, rules in self._in_info_rules.items():
            if name not in self._inputs:
                raise KeyError(f"No input named '{name}' to apply info transfer rule.")
            for rule in rules:
                self._check_rule(rule)

        for name, rules in self._out_info_rules.items():
            if name not in self._outputs:
                raise KeyError(f"No output named '{name}' to apply info transfer rule.")
            for rule in rules:
                self._check_rule(rule)

    def _check_rule(self, rule):
        if isinstance(rule, FromInput):
            if rule.name not in self._inputs:
                raise KeyError(
                    f"No input named '{rule.name}' to use in info transfer rule."
                )
        elif isinstance(rule, FromOutput):
            if rule.name not in self._outputs:
                raise KeyError(
                    f"No output named '{rule.name}' to use in info transfer rule."
                )
        elif not isinstance(rule, FromValue):
            raise TypeError(
                f"Rules must be one of the types FromInput, FromOutput or FromValue. "
                f"Got '{rule.__class__.__name__}'."
            )

    @property
    def logger(self):
        """Logger for this component."""
        return logging.getLogger(self.logger_name)

    @property
    def logger_name(self):
        """Logger name derived from base logger name and class name."""
        base_logger = logging.getLogger(self.base_logger_name)
        # logger hierarchy indicated by "." in name
        return ".".join(([base_logger.name, self.__class__.__name__]))

    @property
    def uses_base_logger_name(self):
        """Whether this class has a ``base_logger_name`` attribute. True."""
        return True

    @property
    def inputs(self):
        """dict: The component's inputs."""
        return self._inputs

    @property
    def outputs(self):
        """dict: The component's outputs."""
        return self._outputs

    @property
    def in_infos(self):
        """dict: The exchanged input infos so far. May contain None values."""
        return self._exchanged_in_infos

    @property
    def out_infos(self):
        """dict: The exchanged output infos so far. May contain None values."""
        return self._exchanged_out_infos

    @property
    def in_data(self):
        """dict: The pulled input data so far. May contain None values."""
        return self._pulled_data

    @property
    def all_data_pulled(self):
        """bool: True if all expected data is pulled."""
        return all(data is not None for data in self.in_data.values())

    @property
    def infos_pushed(self):
        """dict: If an info was pushed for outputs so far."""
        return self._pushed_infos

    @property
    def data_pushed(self):
        """dict: If data was pushed for outputs so far."""
        return self._pushed_data

    @property
    def data_required(self):
        """dict: If data to push is still required."""
        return {
            name: not pushed and name not in self._out_data_cache
            for name, pushed in self.data_pushed.items()
        }

    @property
    def in_infos_required(self):
        """dict: If input infos to exchange are still required."""
        return {
            name: inf is None
            and self.inputs[name].info is None
            and name not in self._in_info_cache
            and name not in self._in_info_rules
            for name, inf in self.in_infos.items()
        }

    @property
    def out_infos_required(self):
        """dict: If output infos to push are still required."""
        return {
            name: not pushed
            and name not in self._out_info_cache
            and name not in self._out_info_rules
            for name, pushed in self.infos_pushed.items()
        }

    def connect(self, start_time, exchange_infos=None, push_infos=None, push_data=None):
        """Exchange the info and data with linked components.

        Values passed by the arguments are cached internally for later calls to the method
        if constructed with ``cache=True`` (the default).
        Thus, it is sufficient to provide only data and infos that became newly available.
        Giving the same data or infos repeatedly overwrites the cache.

        Parameters
        ----------
        start_time : :class:`datetime <datetime.datetime>`
            the composition's starting time as passed to :meth:`.Component.try_connect`
        exchange_infos : dict
            currently or newly available input data infos by input name
        push_infos : dict
            currently or newly available output data infos by output name
        push_data : dict
            currently or newly available output data by output name

        Returns
        -------
        ComponentStatus
            the new component status
        """

        exchange_infos = exchange_infos or {}
        push_infos = push_infos or {}
        push_data = push_data or {}

        with ErrorLogger(self.logger):
            self._check_names(exchange_infos, push_infos, push_data)
            self._check_in_rules(exchange_infos, push_infos)

        exchange_infos = {
            k: v for k, v in exchange_infos.items() if self.in_infos[k] is None
        }
        push_infos = {k: v for k, v in push_infos.items() if self.out_infos[k] is None}
        push_data = {k: v for k, v in push_data.items() if not self.data_pushed[k]}

        # Try to generate infos from transfer rules
        with ErrorLogger(self.logger):
            exchange_infos.update(self._apply_in_info_rules())
            push_infos.update(self._apply_out_info_rules())

        if self._cache:
            self._in_info_cache.update(exchange_infos)
            self._out_info_cache.update(push_infos)
            self._out_data_cache.update(push_data)
        else:
            self._in_info_cache = exchange_infos
            self._out_info_cache = push_infos
            self._out_data_cache = push_data

        any_done = self._exchange_in_infos()

        for name, info in self.out_infos.items():
            if info is None:
                try:
                    self.out_infos[name] = self.outputs[name].info
                    any_done = True
                    self.logger.trace("Successfully pulled output info for %s", name)
                except FinamNoDataError:
                    self.logger.trace("Failed to pull output info for %s", name)

        any_done += self._push(start_time)

        for name, data in self.in_data.items():
            if data is None:
                info = self.in_infos[name]
                if info is not None:
                    try:
                        self.in_data[name] = self.inputs[name].pull_data(
                            start_time or info.time
                        )
                        any_done = True
                        self.logger.trace("Successfully pulled input data for %s", name)
                    except FinamNoDataError:
                        self.logger.trace("Failed to pull input data for %s", name)

        if (
            all(v is not None for v in self.in_infos.values())
            and all(v is not None for v in self.out_infos.values())
            and all(v is not None for v in self.in_data.values())
            and all(v for v in self.infos_pushed.values())
            and all(v for v in self.data_pushed.values())
        ):
            with ErrorLogger(self.logger):
                _check_times(self.out_infos)

            return ComponentStatus.CONNECTED

        if any_done:
            return ComponentStatus.CONNECTING

        return ComponentStatus.CONNECTING_IDLE

    def _apply_in_info_rules(self):
        exchange_infos = {}
        for name, rules in self._in_info_rules.items():
            if self.in_infos[name] is None and name not in self._in_info_cache:
                try:
                    info = self._apply_rules(rules)
                    exchange_infos[name] = info
                except MissingInfoError:
                    pass
        return exchange_infos

    def _apply_out_info_rules(self):
        push_infos = {}
        for name, rules in self._out_info_rules.items():
            if not self.infos_pushed[name] and name not in self._out_info_cache:
                try:
                    info = self._apply_rules(rules)
                    push_infos[name] = info
                except MissingInfoError:
                    pass
        return push_infos

    def _check_names(self, exchange_infos, push_infos, push_data):
        for name in exchange_infos:
            if name not in self._inputs:
                raise KeyError(
                    f"No input named '{name}' available to exchange info for."
                )
        for name in push_infos:
            if name not in self._outputs:
                raise KeyError(f"No output named '{name}' available to push info.")
        for name in push_data:
            if name not in self._outputs:
                raise KeyError(f"No output named '{name}' available to push data.")

    def _check_in_rules(self, exchange_infos, push_infos):
        for name in exchange_infos:
            if name in self._in_info_rules:
                raise ValueError(
                    f"There are info transfer rules given for input `{name}`. "
                    f"Can't provide the info directly."
                )
        for name in push_infos:
            if name in self._out_info_rules:
                raise ValueError(
                    f"There are info transfer rules given for output `{name}`. "
                    f"Can't provide the info directly."
                )

    def _exchange_in_infos(self):
        any_done = False
        for name, info in self._exchanged_in_infos.items():
            if info is None and self.inputs[name].info is not None:
                try:
                    self.in_infos[name] = self.inputs[name].exchange_info()
                    any_done = True
                    self.logger.trace("Successfully exchanged input info for %s", name)
                except FinamNoDataError:
                    self.logger.trace("Failed to exchange input info for %s", name)

        for name, info in list(self._in_info_cache.items()):
            if self.in_infos[name] is None:
                try:
                    inf = self.inputs[name].info
                    self.in_infos[name] = self.inputs[name].exchange_info(
                        None if inf is not None else info
                    )
                    any_done = True
                    self._in_info_cache.pop(name)
                    self.logger.trace("Successfully exchanged input info for %s", name)
                except FinamNoDataError:
                    self.logger.trace("Failed to exchange input info for %s", name)

        return any_done

    def _push(self, time):
        any_done = False

        for name, info in list(self._out_info_cache.items()):
            if not self.infos_pushed[name]:
                self.outputs[name].push_info(info)
                self.infos_pushed[name] = True
                any_done = True
                self._out_info_cache.pop(name)
                self.logger.trace("Successfully pushed output info for %s", name)

        for name, data in list(self._out_data_cache.items()):
            if not self.data_pushed[name] and self.infos_pushed[name]:
                info = self.out_infos[name]
                if info is not None:
                    self._push_data(name, data, time, info.time)
                    any_done = True

        return any_done

    def _push_data(self, name, data, time, info_time):
        out = self.outputs[name]
        if out.is_static:
            out.push_data(data, None)
        elif info_time != time:
            out.push_data(data, time)
            out.push_data(copy.copy(data), info_time)
        else:
            out.push_data(data, info_time)

        self.data_pushed[name] = True
        self._out_data_cache.pop(name)
        self.logger.trace("Successfully pushed output data for %s", name)


def _check_times(infos):
    t = None
    for _, info in infos.items():
        if t is None:
            t = info.time
        elif t != info.time:
            raise FinamTimeError("Input infos have different starting times.")


def _transfer_fields(source_info, target_info, fields):
    if len(fields) == 0:
        target_info.time = source_info.time
        target_info.grid = source_info.grid
        target_info.meta = copy.copy(source_info.meta)
    else:
        for field in fields:
            if field == "time":
                target_info.time = source_info.time
            elif field == "grid":
                target_info.grid = source_info.grid
            else:
                target_info.meta[field] = source_info.meta[field]
