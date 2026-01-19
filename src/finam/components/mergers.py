"""Pull-based components for merging multiple inputs into a single output"""

import copy

import numpy as np

from finam.interfaces import ComponentStatus

from ..data.tools import (
    Mask,
    compatible_units,
    filled,
    is_sub_mask,
    mask_specified,
    strip_time,
    to_masked,
)
from ..errors import FinamMetaDataError
from ..sdk import CallbackOutput, Component
from ..tools.log_helper import ErrorLogger


class WeightedSum(Component):
    """Pull-based component to merge inputs by weighted sum.

    This component does not have an own time step.
    Execution is triggered by downstream pulls.

    .. code-block:: text

                             +-------------------+
      --> [<custom1>       ] |                   |
      --> [<custom1>_weight] |                   |
      --> [<custom2>       ] | CallbackComponent | [WeightedSum] -->
      --> [<custom2>_weight] |                   |
      --> [....            ] |                   |
                             +-------------------+

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        component = fm.components.WeightedSum(inputs=["A", "B", "C"])

        # ... create and initialize composition

        # comp_1.outputs["Value"] >> component.inputs["A"]
        # comp_1.outputs["Weight"] >> component.inputs["A_weight"]
        # ...

    .. testcode:: constructor
        :hide:

        component.initialize()

    Parameters
    ----------
    inputs : list(str)
        Base input names; will create two inputs for each entry: "<name>" and "<name>_weight"
    start : :class:`datetime <datetime.datetime>`
        Starting time, for initial data exchange
    grid : GridBase or None
        Expected input grid specification; tries to obtain grid specs from inputs if set to None
    """

    def __init__(self, inputs, grid=None):
        super().__init__()
        self._input_names = inputs
        self._grid = grid
        self._units = None
        self._in_data = None
        self._weights = None
        self._out_data = None
        self._last_update = None

    def _initialize(self):
        for name in self._input_names:
            self.inputs.add(
                name=name, time=None, grid=self._grid, units=None, mask=None
            )
            self.inputs.add(
                name=name + "_weight",
                time=None,
                grid=self._grid,
                units="",
                mask=None,
                static=True,
            )

        self._grid = None

        self.outputs.add(CallbackOutput(callback=self._get_data, name="WeightedSum"))
        self.create_connector(pull_data=list(self.inputs))

    def _connect(self, start_time):
        if (
            self.connector.all_data_pulled
            and not self.connector.infos_pushed["WeightedSum"] is None
        ):
            self._check_infos()
            push_infos = self._create_out_info()
            self.try_connect(start_time, push_infos=push_infos)
        else:
            self.try_connect(start_time)

        if self.status == ComponentStatus.CONNECTED:
            self._in_data = {}
            self._weights = {}
            for name in self._input_names:
                self._in_data[name] = self.connector.in_data[name]
                self._weights[name] = self.connector.in_data[name + "_weight"]
            self._normalize_weights()

    def _check_infos(self):
        for name in self._input_names:
            info = self.connector.in_infos[name]

            if info is not None:
                self._check_grid(info)
                self._compatible_units(info)
            if not mask_specified(info.mask) and info.mask == Mask.FLEX:
                with ErrorLogger(self.logger):
                    msg = "Mask type FLEX not supported."
                    raise FinamMetaDataError(msg)

            weight_info = self.connector.in_infos[name + "_weight"]
            if weight_info is not None:
                self._check_grid(weight_info)
            if not mask_specified(weight_info.mask) and weight_info.mask == Mask.FLEX:
                with ErrorLogger(self.logger):
                    msg = "Mask type FLEX not supported for weights."
                    raise FinamMetaDataError(msg)

            if mask_specified(weight_info.mask) and not is_sub_mask(
                weight_info.mask, info.mask
            ):
                with ErrorLogger(self.logger):
                    msg = "Data mask must be a sub-mask of weight mask."
                    raise FinamMetaDataError(msg)

    def _create_out_info(self):
        base_info = None
        for name in self._input_names:
            info = self.connector.in_infos[name]
            if info is not None:
                if base_info is None:
                    base_info = info.copy_with()

        out_mask = base_info.mask
        for name in self._input_names:
            info = self.connector.in_infos[name]
            mask = info.mask
            if not mask_specified(mask):
                out_mask = Mask.NONE
                break
            out_mask &= mask

        return {"WeightedSum": base_info.copy_with(mask=out_mask)}

    def _check_grid(self, info):
        if self._grid is None:
            self._grid = info.grid
        else:
            if self._grid != info.grid:
                with ErrorLogger(self.logger):
                    raise FinamMetaDataError("All inputs must have the same grid.")

    def _compatible_units(self, info):
        if self._units is None:
            self._units = info.units
        else:
            if not compatible_units(self._units, info.units):
                with ErrorLogger(self.logger):
                    raise FinamMetaDataError(
                        "All value inputs must have the same dimensions."
                    )

    def _normalize_weights(self):
        weights_sum = None
        for name in self._input_names:
            weight = strip_time(self._weights[name], self._grid)

            if weights_sum is None:
                weights_sum = copy.copy(weight)
            else:
                weights_sum += weight

        for name in self._input_names:
            weight = strip_time(self._weights[name], self._grid)
            self._weights[name] = np.nan_to_num(weight / weights_sum, 0.0)

    def _validate(self):
        pass

    def _update(self):
        pass

    def _finalize(self):
        pass

    def _get_data(self, _caller, time):
        if self._in_data is None:
            return None

        if time != self._last_update:
            if self.status == ComponentStatus.VALIDATED:
                for name in self._input_names:
                    self._in_data[name] = self.inputs[name].pull_data(time)

            result = None
            mask = self._outputs["WeightedSum"].info.mask

            for name in self._input_names:
                value = strip_time(self._in_data[name], self._grid)
                weight = self._weights[name]

                # Treat masked values as zero weight
                v = filled(value, 0.0)
                w = filled(weight, 0.0)

                if result is None:
                    result = v * w
                else:
                    result += v * w

            if not mask_specified(mask):
                self._out_data = result
            else:
                self._out_data = to_masked(result, mask=mask)

            self._last_update = time

        return self._out_data
