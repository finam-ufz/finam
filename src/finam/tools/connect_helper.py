"""Iterative connection helpers."""
from ..core.interfaces import ComponentStatus, FinamNoDataError


class ConnectHelper:
    """
    Helper for iterative connect

    Parameters
    ----------
    logger : Logger
        Logger to use
    inputs : dict
        All inputs of the component.
    outputs : dict
        All outputs of the component.
    required_in_data : arraylike
        Names of the inputs that are to be pulled
    required_out_infos : arraylike
        Names of the outputs that need exchanged info
    """

    def __init__(self, logger, inputs, outputs, required_in_data=None, required_out_infos=None):

        self.logger = logger
        self._inputs = inputs
        self._outputs = outputs

        self._exchanged_in_infos = {name: None for name in self.inputs.keys()}
        self._exchanged_out_infos = {name: None for name in required_out_infos or []}

        self._pulled_data = {name: None for name in required_in_data or []}

        self._pushed_infos = {
            name: outp.has_info() for name, outp in self.outputs.items()
        }
        self._pushed_data = {name: False for name in self.outputs.keys()}

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

        exchange_infos = exchange_infos or {}
        push_infos = push_infos or {}
        push_data = push_data or {}

        any_done = self._push(time, push_infos, push_data)
        any_done |= self._exchange_in_infos(exchange_infos)

        for name, info in self.out_infos.items():
            if info is None:
                try:
                    self.out_infos[name] = self.outputs[name].info
                    any_done = True
                    self.logger.debug(f"Successfully pulled output info for {name}")
                except FinamNoDataError:
                    self.logger.debug(f"Failed to pull output info for {name}")
                    pass

        for name, data in self.in_data.items():
            if data is None:
                try:
                    self.in_data[name] = self.inputs[name].pull_data(time)
                    any_done = True
                    self.logger.debug(f"Successfully pulled input data for {name}")
                except FinamNoDataError:
                    self.logger.debug(f"Failed to pull input data for {name}")
                    pass

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

    def _exchange_in_infos(self, exchange_infos):
        any_done = False
        for name, info in self._exchanged_in_infos.items():
            if info is None and self.inputs[name].info is not None:
                try:
                    self.in_infos[name] = self.inputs[name].exchange_info()
                    any_done = True
                    self.logger.debug(f"Successfully exchanged input info for {name}")
                except FinamNoDataError:
                    self.logger.debug(f"Failed to exchange input info for {name}")
                    pass

        for name, info in exchange_infos.items():
            if self.in_infos[name] is None:
                try:
                    inf = self.inputs[name].info
                    self.in_infos[name] = self.inputs[name].exchange_info(
                        None if inf is not None else info
                    )
                    any_done = True
                    self.logger.debug(f"Successfully exchanged input info for {name}")
                except FinamNoDataError:
                    self.logger.debug(f"Failed to exchange input info for {name}")
                    pass

        return any_done

    def _push(self, time, push_infos, push_data):
        any_done = False

        for name, info in push_infos.items():
            if not self.infos_pushed[name]:
                self.outputs[name].push_info(info)
                self.infos_pushed[name] = True
                any_done = True
                self.logger.debug(f"Successfully pushed output info for {name}")

        for name, data in push_data.items():
            if not self.data_pushed[name] and self.infos_pushed[name]:
                try:
                    self.outputs[name].push_data(data, time)
                    self.data_pushed[name] = True
                    any_done = True
                    self.logger.debug(f"Successfully pushed output data for {name}")
                except FinamNoDataError:
                    self.logger.debug(f"Failed to push output data for {name}")

        return any_done
