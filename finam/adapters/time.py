from core.sdk import AAdapter
from data.grid import Grid


class NextValue(AAdapter):
    """
    Time interpolation providing the next future value.
    """

    def __init__(self):
        super().__init__()
        self.data = None

    def source_changed(self, time):
        data = self.pull_data(time)
        self.data = data

    def get_data(self, time):
        return self.data


class PreviousValue(AAdapter):
    """
    Time interpolation providing the newest past value.
    """

    def __init__(self):
        super().__init__()
        self.old_data = None
        self.new_data = None

    def source_changed(self, time):
        data = self.pull_data(time)
        if self.new_data is None:
            self.old_data = (time, data)
        else:
            self.old_data = self.new_data

        self.new_data = (time, data)

    def get_data(self, time):
        if time < self.new_data[0]:
            return self.old_data[1]
        else:
            return self.new_data[1]


class LinearInterpolation(AAdapter):
    """
    Linear time interpolation.
    """

    def __init__(self):
        super().__init__()
        self.old_data = None
        self.new_data = None

    def source_changed(self, time):
        self.old_data = self.new_data
        self.new_data = (time, self.pull_data(time))

    def get_data(self, time):
        if self.old_data is None:
            return self.new_data[1]

        dt = (time - self.old_data[0]) / float(self.new_data[0] - self.old_data[0])

        o = self.old_data[1]
        n = self.new_data[1]

        if (isinstance(o, int) or isinstance(o, float)) and (
            isinstance(n, int) or isinstance(n, float)
        ):
            return _interpolate(o, n, dt)
        elif isinstance(o, Grid) and isinstance(n, Grid):
            result = Grid.create_like(o)
            for i in range(len(result.data)):
                result.data[i] = _interpolate(o.data[i], n.data[i], dt)

            return result
        else:
            raise Exception(
                f"Unsupported/incompatible data types in LinearInterpolation: {o.__class__.__name__}, {n.__class__.__name__}"
            )


class LinearIntegration(AAdapter):
    """
    Time integration over the last time step of the requester.
    """

    @classmethod
    def sum(cls):
        """
        Create a new time integration providing the sum over time (i.e. integral).
        """
        return LinearIntegration(normalize=False)

    @classmethod
    def mean(cls):
        """
        Create a new time integration providing the mean over time.
        """
        return LinearIntegration(normalize=True)

    def __init__(self, normalize=True):
        super().__init__()
        self.data = []
        self.prev_time = 0
        self.normalize = normalize

    def source_changed(self, time):
        data = self.pull_data(time)
        self.data.append((time, data))

    def get_data(self, time):
        if len(self.data) == 1:
            return self.data[0][1]

        if time <= self.data[0][0]:
            return self.data[0][1]

        sum_value = 0.0

        for i in range(len(self.data) - 1):
            t_old, v_old = self.data[i]
            t_new, v_new = self.data[i + 1]

            if self.prev_time >= t_new:
                continue
            if time <= t_old:
                break

            scale = t_new - t_old
            dt1 = max((self.prev_time - t_old) / scale, 0.0)
            dt2 = min((time - t_old) / scale, 1.0)

            v1 = _interpolate(v_old, v_new, dt1)
            v2 = _interpolate(v_old, v_new, dt2)

            sum_value += (dt2 - dt1) * scale * 0.5 * (v1 + v2)

        if self.normalize:
            dt = time - self.prev_time
            if dt > 0:
                sum_value /= dt

        if len(self.data) > 2:
            self.data = self.data[-2:]

        self.prev_time = time

        return sum_value


def _interpolate(old_value, new_value, dt):
    return old_value + dt * (new_value - old_value)
