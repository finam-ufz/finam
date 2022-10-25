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

    def __init__(
        self,
        info=None,
        frequency=1.0,
        time_frequency=1.0,
        octaves=1,
        persistence=0.5,
        low=-1,
        high=1,
        seed=0,
    ):
        super().__init__()

        self._info = info or Info(time=None, grid=None, units=None)
        self._seed = seed

        self._frequency = frequency
        self._time_frequency = time_frequency
        self._persistence = persistence
        self._low = low
        self._high = high
        self._octaves = octaves

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

        amp = 1.0
        max_amp = 0.0
        freq = self._frequency
        freq_t = self._time_frequency

        if isinstance(grid, UnstructuredGrid):
            func = self._generate_unstructured
        else:
            func = self._generate_structured

        data = func(grid, t * freq_t, freq, ox)
        max_amp += amp
        amp *= self._persistence
        freq *= 0.5
        freq_t *= 0.5

        for i in range(self._octaves - 1):
            data += amp * func(grid, t * freq_t, freq, ox)
            max_amp += amp
            amp *= self._persistence
            freq *= 0.5
            freq_t *= 0.5

        data /= max_amp
        data = data * (self._high - self._low) / 2 + (self._high + self._low) / 2

        return data

    def _generate_structured(self, grid, t, freq, ox):

        if grid.dim == 1:
            data = ox.noise2array(grid.data_axes[0] * freq, np.asarray([t]))
        if grid.dim == 2:
            data = ox.noise3array(
                grid.data_axes[0] * freq, grid.data_axes[1] * freq, np.asarray([t])
            )
        if grid.dim == 3:
            data = ox.noise4array(
                grid.data_axes[0] * freq,
                grid.data_axes[1] * freq,
                grid.data_axes[2] * freq,
                np.asarray([t]),
            )
        return data[0, ...].T

    def _generate_unstructured(self, grid, t, freq, ox):

        points = grid.data_points
        data = np.full((grid.point_count,), 0.0, dtype=float)

        if grid.dim == 1:
            for i, p in enumerate(points):
                data[i] = ox.noise2(p[0] * freq, t)
        elif grid.dim == 2:
            for i, p in enumerate(points):
                data[i] = ox.noise3(p[0] * freq, p[1] * freq, t)
        elif grid.dim == 3:
            for i, p in enumerate(points):
                data[i] = ox.noise4(p[0] * freq, p[1] * freq, p[2] * freq, t)

        return data
