"""Parametric grid generator components"""
import numpy as np

from finam.data.grid_base import Grid
from finam.data.grid_spec import NoGrid, StructuredGrid
from finam.data.tools import Info
from finam.errors import FinamMetaDataError
from finam.interfaces import ComponentStatus
from finam.sdk import CallbackOutput, Component, Output
from finam.tools import ErrorLogger


class ParametricGrid(Component):
    """Pull-based parametric grid generator.

    Generates grids with values filled from a function of time and cell coordinates.

    .. code-block:: text

        +----------------+
        |                |
        | ParametricGrid | [Grid] -->
        |                |
        +----------------+

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        component = fm.components.ParametricGrid(
            info=fm.Info(time=None, grid=fm.UniformGrid((20, 15))),
            func=lambda t, x, y: x * y,
        )

    .. testcode:: constructor
        :hide:

        component.initialize()

    Parameters
    ----------
    info : Info, optional
        Output metadata info. All values are taken from the target if not specified.
    func : callable
        A callable with the signature func(t, x[, y[, z]]) -> Quantity
    """

    def __init__(
        self,
        info=None,
        func=None,
    ):
        super().__init__()

        self._info = info or Info(time=None, grid=None, units=None)
        self._func = func
        self._is_ready = False

    def _initialize(self):
        self.outputs.add(
            io=CallbackOutput(
                callback=self._generate_grid, name="Grid", info=self._info
            )
        )
        self.create_connector()

    def _connect(self, start_time):
        self.try_connect(start_time)

        info = self.connector.out_infos["Grid"]
        if info is not None:
            failed = isinstance(info.grid, NoGrid)
            failed |= isinstance(info.grid, Grid) and not 1 <= info.grid.dim <= 3
            if failed:
                with ErrorLogger(self.logger):
                    raise FinamMetaDataError(
                        f"Can generate parametric grids only for gridded 1D-3D data. "
                        f"Got {info.grid}"
                    )

            self._info = info
            self._is_ready = True

    def _validate(self):
        pass

    def _update(self):
        pass

    def _finalize(self):
        pass

    def _generate_grid(self, _caller, time):
        if not self._is_ready:
            return None

        return _generate_grid(self._info.grid, time, self._func)


class StaticParametricGrid(Component):
    """Static parametric grid generator.

    Generates a grid with values filled from a function of cell coordinates.

    .. code-block:: text

        +----------------------+
        |                      |
        | StaticParametricGrid | [Grid] -->
        |                      |
        +----------------------+

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        component = fm.components.StaticParametricGrid(
            info=fm.Info(time=None, grid=fm.UniformGrid((20, 15))),
            func=lambda x, y: x * y,
        )

    .. testcode:: constructor
        :hide:

        component.initialize()

    Parameters
    ----------
    info : Info, optional
        Output metadata info. All values are taken from the target if not specified.
    func : callable
        A callable with the signature func(x[, y[, z]]) -> Quantity
    """

    def __init__(
        self,
        info=None,
        func=None,
    ):
        super().__init__()

        self._info = info or Info(time=None, grid=None, units=None)
        self._func = func

        self._is_ready = False

    def _initialize(self):
        self.outputs.add(io=Output(name="Grid", static=True, info=self._info))
        self.create_connector()

    def _connect(self, start_time):
        push_data = {}
        if self.connector.out_infos["Grid"] is not None:
            push_data["Grid"] = self._generate_grid()

        self.try_connect(start_time, push_data=push_data)

        info = self.connector.out_infos["Grid"]
        if info is not None:
            failed = isinstance(info.grid, NoGrid)
            failed |= isinstance(info.grid, Grid) and not 1 <= info.grid.dim <= 3
            if failed:
                with ErrorLogger(self.logger):
                    raise FinamMetaDataError(
                        f"Can generate parametric grid only for gridded 1D-3D data. "
                        f"Got {info.grid}"
                    )

            self._info = info
            self._is_ready = True

    def _validate(self):
        self.status = ComponentStatus.FINISHED

    def _update(self):
        pass

    def _finalize(self):
        pass

    def _generate_grid(self):
        return _generate_grid(self._info.grid, None, self._func)


def _generate_grid(grid, time, cell_func):
    points = grid.data_points
    data = np.full((points.shape[0],), 0.0, dtype=float)

    if time is None:
        for i, p in enumerate(points):
            data[i] = cell_func(*p)
    else:
        for i, p in enumerate(points):
            data[i] = cell_func(time, *p)

    if isinstance(grid, StructuredGrid):
        data = np.reshape(data, newshape=grid.data_shape, order=grid.order)

    return data
