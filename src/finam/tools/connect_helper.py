"""Iterative connection helpers."""
import logging

from finam.interfaces import ComponentStatus, Loggable

from ..errors import FinamNoDataError
from ..tools.log_helper import ErrorLogger


class ConnectHelper(Loggable):
    """Helper for iterative connect.

    Warning:
        This class is not intended for direct use!
        Use :meth:`.Components.create_connector` and :meth:`.Components.try_connect` instead.

    Parameters
    ----------
    logger : Logger
        Logger to use
    inputs : dict
        All inputs of the component.
    outputs : dict
        All outputs of the component.
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
        cache=True,
    ):

        self.base_logger_name = logger_name
        self._inputs = inputs
        self._outputs = outputs
        self._cache = cache

        with ErrorLogger(self.logger):
            for name in pull_data or []:
                if name not in self._inputs:
                    raise ValueError(
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

        self._in_info_cache = {}
        self._out_info_cache = {}
        self._out_data_cache = {}

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
    def infos_pushed(self):
        """dict: If an info was pushed for outputs so far."""
        return self._pushed_infos

    @property
    def data_pushed(self):
        """dict: If data was pushed for outputs so far."""
        return self._pushed_data

    def connect(self, time, exchange_infos=None, push_infos=None, push_data=None):
        """Exchange the info and data with linked components.

        Values passed by the arguments are cached internally for later calls to the method
        if constructed with ``cache=True`` (the default).
        Thus, it is sufficient to provide only data and infos that became newly available.
        Giving the same data or infos repeatedly overwrites the cache.

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

        exchange_infos = {
            k: v for k, v in exchange_infos.items() if self.in_infos[k] is None
        }
        push_infos = {k: v for k, v in push_infos.items() if self.out_infos[k] is None}
        push_data = {k: v for k, v in push_data.items() if not self.data_pushed[k]}

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
                    self.logger.debug("Successfully pulled output info for %s", name)
                except FinamNoDataError:
                    self.logger.debug("Failed to pull output info for %s", name)

        any_done += self._push(time)

        for name, data in self.in_data.items():
            if data is None:
                info = self.in_infos[name]
                if info is not None:
                    try:
                        self.in_data[name] = self.inputs[name].pull_data(
                            time or info.time
                        )
                        any_done = True
                        self.logger.debug("Successfully pulled input data for %s", name)
                    except FinamNoDataError:
                        self.logger.debug("Failed to pull input data for %s", name)

        if (
            all(v is not None for v in self.in_infos.values())
            and all(v is not None for v in self.out_infos.values())
            and all(v is not None for v in self.in_data.values())
            and all(v for v in self.infos_pushed.values())
            and all(v for v in self.data_pushed.values())
        ):
            return ComponentStatus.CONNECTED

        if any_done:
            return ComponentStatus.CONNECTING

        return ComponentStatus.CONNECTING_IDLE

    def _check_names(self, exchange_infos, push_infos, push_data):
        for name in exchange_infos:
            if name not in self._inputs:
                raise ValueError(
                    f"No input named '{name}' available to exchange info for."
                )
        for name in push_infos:
            if name not in self._outputs:
                raise ValueError(f"No output named '{name}' available to push info.")
        for name in push_data:
            if name not in self._outputs:
                raise ValueError(f"No output named '{name}' available to push data.")

    def _exchange_in_infos(self):
        any_done = False
        for name, info in self._exchanged_in_infos.items():
            if info is None and self.inputs[name].info is not None:
                try:
                    self.in_infos[name] = self.inputs[name].exchange_info()
                    any_done = True
                    self.logger.debug("Successfully exchanged input info for %s", name)
                except FinamNoDataError:
                    self.logger.debug("Failed to exchange input info for %s", name)

        for name, info in list(self._in_info_cache.items()):
            if self.in_infos[name] is None:
                try:
                    inf = self.inputs[name].info
                    self.in_infos[name] = self.inputs[name].exchange_info(
                        None if inf is not None else info
                    )
                    any_done = True
                    self._in_info_cache.pop(name)
                    self.logger.debug("Successfully exchanged input info for %s", name)
                except FinamNoDataError:
                    self.logger.debug("Failed to exchange input info for %s", name)

        return any_done

    def _push(self, time):
        any_done = False

        for name, info in list(self._out_info_cache.items()):
            if not self.infos_pushed[name]:
                self.outputs[name].push_info(info)
                self.infos_pushed[name] = True
                any_done = True
                self._out_info_cache.pop(name)
                self.logger.debug("Successfully pushed output info for %s", name)

        for name, data in list(self._out_data_cache.items()):
            if not self.data_pushed[name] and self.infos_pushed[name]:
                info = self.out_infos[name]
                if info is not None:
                    try:
                        self.outputs[name].push_data(data, time or info.time)
                        self.data_pushed[name] = True
                        any_done = True
                        self._out_data_cache.pop(name)
                        self.logger.debug(
                            "Successfully pushed output data for %s", name
                        )
                    except FinamNoDataError:
                        self.logger.debug("Failed to push output data for %s", name)

        return any_done
