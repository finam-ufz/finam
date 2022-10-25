"""Noise generator components"""
import datetime as dt

import numpy as np

from finam.data.grid_spec import NoGrid, UnstructuredGrid
from finam.data.tools import Info
from finam.errors import FinamMetaDataError
from finam.sdk import CallbackOutput, Component
from finam.tools import ErrorLogger


class SimplexNoise(Component):
    """Pull-based simplex noise generator.

    Requires `opensimplex <https://pypi.org/project/opensimplex/>`_ to be installed.

    .. code-block:: text

        +--------------+
        |              |
        | SimplexNoise | [Noise] -->
        |              |
        +--------------+

    """

    def __init__(self, info=None, seed=0):
        super().__init__()

        self._info = info or Info(time=None, grid=None, units=None)
        self._seed = seed
        self._is_ready = False

    def _initialize(self):
        self.outputs.add(
            io=CallbackOutput(
                callback=self._generate_noise, name="Noise", info=self._info
            )
        )
        self.create_connector()

    def _connect(self):
        self.try_connect()

        info = self.connector.out_infos["Noise"]
        if info is not None:
            if isinstance(info.grid, NoGrid):
                with ErrorLogger(self.logger):
                    raise FinamMetaDataError(
                        "Can't generate simplex noise for 'NoGrid' data."
                    )

            self._info = info
            self._is_ready = True

    def _validate(self):
        pass

    def _update(self):
        pass

    def _finalize(self):
        pass

    def _generate_noise(self, _caller, time):
        if not self._is_ready:
            return None

        with ErrorLogger(self.logger):
            try:
                import opensimplex as ox
            except ModuleNotFoundError:
                self.logger.error(
                    "Package 'opensimplex' required. Try:\npip install opensimplex"
                )
                raise

        ox.seed(self._seed)

        grid = self._info.grid
        t = (time - dt.datetime(1900, 1, 1)).total_seconds()

        if isinstance(grid, UnstructuredGrid):
            return self._generate_unstructured(grid, t, ox)
        else:
            return self._generate_structured(grid, t, ox)

    def _generate_structured(self, grid, t, ox):
        if grid.dim == 1:
            data = ox.noise2array(grid.data_axes[0], np.asarray([t]))
        if grid.dim == 2:
            data = ox.noise3array(grid.data_axes[0], grid.data_axes[1], np.asarray([t]))
        if grid.dim == 3:
            data = ox.noise4array(
                grid.data_axes[0],
                grid.data_axes[1],
                grid.data_axes[2],
                np.asarray([t]),
            )
        return data[0, ...].T

    def _generate_unstructured(self, grid, t, ox):
        points = grid.data_points
        funcs = {
            1: ox.noise2,
            2: ox.noise3,
            3: ox.noise4,
        }
        func = funcs[grid.dim]
        data = np.full((grid.point_count,), 0.0, dtype=float)

        for i, p in enumerate(points):
            data[i] = func(*p, t)

        return data
