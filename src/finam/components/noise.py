"""Noise generator components"""
import datetime as dt

import numpy as np
import opensimplex as ox

from finam.data.grid_base import Grid
from finam.data.grid_spec import NoGrid, UnstructuredGrid
from finam.data.tools import Info
from finam.errors import FinamMetaDataError
from finam.interfaces import ComponentStatus
from finam.sdk import CallbackOutput, Component, Output
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

        component = fm.components.SimplexNoise(
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

    def _connect(self, start_time):
        self.try_connect(start_time)

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

        return _generate_noise(
            grid,
            t,
            self._frequency,
            self._time_frequency,
            self._octaves,
            self._persistence,
            self._low,
            self._high,
        )


class StaticSimplexNoise(Component):
    """Static simplex noise generator.

    Requires `opensimplex <https://pypi.org/project/opensimplex/>`_ to be installed.

    .. code-block:: text

        +--------------------+
        |                    |
        | StaticSimplexNoise | [Noise] -->
        |                    |
        +--------------------+

    Examples
    --------

    .. testcode:: constructor

        import finam as fm

        component = fm.components.StaticSimplexNoise(
            info=fm.Info(time=None, grid=fm.UniformGrid((20, 15))),
            frequency=0.1,
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
        self._persistence = persistence
        self._low = low
        self._high = high
        self._octaves = octaves

        self._is_ready = False

    def _initialize(self):
        self.outputs.add(io=Output(name="Noise", static=True, info=self._info))
        self.create_connector()

    def _connect(self, start_time):
        push_data = {}
        if self.connector.out_infos["Noise"] is not None:
            push_data["Noise"] = self._generate_noise()

        self.try_connect(start_time, push_data=push_data)

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
        self.status = ComponentStatus.FINISHED

    def _update(self):
        pass

    def _finalize(self):
        pass

    def _generate_noise(self):
        ox.seed(self._seed)

        grid = self._info.grid

        return _generate_noise(
            grid,
            1,
            self._frequency,
            1,
            self._octaves,
            self._persistence,
            self._low,
            self._high,
        )


def _generate_noise(
    grid, time, frequency, time_frequency, octaves, persistence, low, high
):
    if isinstance(grid, NoGrid):
        func = _generate_scalar
    elif isinstance(grid, UnstructuredGrid):
        func = _generate_unstructured
    else:
        func = _generate_structured

    amp = 1.0
    max_amp = 0.0
    freq = frequency
    freq_t = time_frequency

    for i in range(octaves):
        if i == 0:
            data = func(grid, time * freq_t, freq)
        else:
            data += amp * func(grid, time * freq_t, freq)
        max_amp += amp
        amp *= persistence
        freq *= 2.0
        freq_t *= 2.0

    data /= max_amp
    data = data * (high - low) / 2 + (high + low) / 2
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
    # pylint: disable-next=possibly-used-before-assignment
    return data[0, ...].T


def _generate_unstructured(grid, t, freq):
    points = grid.data_points
    data = np.full((points.shape[0],), 0.0, dtype=float)

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
