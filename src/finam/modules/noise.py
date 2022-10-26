"""Noise generator components"""
import datetime as dt

import numpy as np
import opensimplex as ox

from finam.data.grid_spec import NoGrid, UnstructuredGrid
from finam.data.grid_tools import Grid
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

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        component = fm.modules.SimplexNoise(
            info=fm.Info(time=None, grid=fm.UniformGrid((20, 15))),
            frequency=0.1,
            time_frequency=1 / (24 * 3600),
            octaves=3,
            persistence=0.75,
            low=0.0, high=1.0,
            seed=1234,
        )

    .. testcode:: constructor
        :hide:

        component.initialize()

    Parameters
    ----------
    info : Info, optional
        Output metadata info. All values are taken from the target if not specified.
    frequency : float
        Spatial frequency of the noise, in map units. Default 1.0
    time_frequency : float
        Temporal frequency of the noise, in Hz. Default 1.0
    octaves : int
        Number of octaves. Default 1
    persistence : float, optional
        Persistence over octaves. Default 0.5
    low : float, optional
        Lower limit for values. Default -1.0
    high : float, optional
        Upper limit for values. Default 1.0
    seed : int, optional
        PRNG seed for noise generator. Default 0
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

        if octaves < 1:
            raise ValueError("At least one octave required for SimplexNoise")

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
            failed = isinstance(info.grid, NoGrid) and info.grid.dim > 0
            failed |= isinstance(info.grid, Grid) and not 1 <= info.grid.dim <= 3
            if failed:
                with ErrorLogger(self.logger):
                    raise FinamMetaDataError(
                        f"Can generate simplex noise only for gridded 1D-3D data, or for 0D 'NoGrid' data. "
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

    def _generate_noise(self, _caller, time):
        if not self._is_ready:
            return None

        ox.seed(self._seed)

        grid = self._info.grid
        t = (time - dt.datetime(1900, 1, 1)).total_seconds()

        if isinstance(grid, NoGrid):
            func = _generate_scalar
        elif isinstance(grid, UnstructuredGrid):
            func = _generate_unstructured
        else:
            func = _generate_structured

        amp = 1.0
        max_amp = 0.0
        freq = self._frequency
        freq_t = self._time_frequency

        for i in range(self._octaves):
            if i == 0:
                data = func(grid, t * freq_t, freq)
            else:
                data += amp * func(grid, t * freq_t, freq)
            max_amp += amp
            amp *= self._persistence
            freq *= 2.0
            freq_t *= 2.0

        data /= max_amp
        data = data * (self._high - self._low) / 2 + (self._high + self._low) / 2

        return data


def _generate_scalar(_grid, t, _freq):
    return ox.noise2(0, t)


def _generate_structured(grid, t, freq):
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


def _generate_unstructured(grid, t, freq):

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
