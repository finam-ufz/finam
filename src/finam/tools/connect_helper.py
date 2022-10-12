"""Iterative connection helpers."""
from ..core.interfaces import ComponentStatus, FinamNoDataError


class ConnectHelper:
    """
    Helper for iterative connect

    Parameters
    ----------
    inputs : dict
        All inputs of the component.
    outputs : dict
        All outputs of the component.
    required_in_data : arraylike
        Names of the inputs that are to be pulled
    required_out_infos : arraylike
        Names of the outputs that need exchanged info
    """

    def __init__(self, inputs, outputs, required_in_data=None, required_out_infos=None):

        self._inputs = inputs
        self._outputs = outputs

        self._exchanged_in_infos = {name: None for name in self._inputs.keys()}
        self._exchanged_out_infos = {name: None for name in required_out_infos or []}

        self._pulled_data = {name: None for name in required_in_data or []}

        self._pushed_infos = {
            name: outp.has_info() for name, outp in self._outputs.items()
        }
        self._pushed_data = {name: False for name in self._outputs.keys()}

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
        """Exchange the data info with the input's source.

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

        for name, info in self._exchanged_out_infos.items():
            if info is None:
                try:
                    self._exchanged_out_infos[name] = self._outputs[name].info
                    any_done = True
                except FinamNoDataError:
                    pass

        for name, data in self._pulled_data.items():
            if data is None:
                try:
                    self._pulled_data[name] = self._inputs[name].pull_data(time)
                    any_done = True
                except FinamNoDataError:
                    pass

        if (
            all(v is not None for v in self._exchanged_in_infos.values())
            and all(v is not None for v in self._exchanged_out_infos.values())
            and all(v is not None for v in self._pulled_data.values())
            and all(v for v in self._pushed_infos.values())
            and all(v for v in self._pushed_data.values())
        ):
            return ComponentStatus.CONNECTED

        if any_done:
            return ComponentStatus.CONNECTING

        return ComponentStatus.CONNECTING_IDLE

    def _exchange_in_infos(self, exchange_infos):
        any_done = False
        for name, info in self._exchanged_in_infos.items():
            if info is None and self._inputs[name].info is not None:
                try:
                    self._exchanged_in_infos[name] = self._inputs[name].exchange_info()
                    any_done = True
                except FinamNoDataError:
                    pass

        for name, info in exchange_infos.items():
            if self._exchanged_in_infos[name] is None:
                try:
                    inf = self._inputs[name].info
                    self._exchanged_in_infos[name] = self._inputs[name].exchange_info(
                        None if inf is not None else info
                    )
                    any_done = True
                except FinamNoDataError:
                    pass

        return any_done

    def _push(self, time, push_infos, push_data):
        any_done = False

        for name, info in push_infos.items():
            if not self._pushed_infos[name]:
                self._outputs[name].push_info(info)
                self._pushed_infos[name] = True
                any_done = True

        for name, data in push_data.items():
            if not self._pushed_data[name]:
                self._outputs[name].push_data(data, time)
                self._pushed_data[name] = True
                any_done = True

        return any_done
