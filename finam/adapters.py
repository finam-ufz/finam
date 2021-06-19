from sdk import AAdapter


class NextValue(AAdapter):
    def __init__(self):
        super().__init__("NextValue")
        self.data = None

    def set_data(self, data, time):
        self.data = data

    def get_data(self, time):
        return self.data


class PreviousValue(AAdapter):
    def __init__(self):
        super().__init__("Previous")
        self.old_data = None
        self.new_data = None

    def set_data(self, data, time):
        if self.new_data is None:
            self.old_data = data
        else:
            self.old_data = self.new_data
        self.new_data = data

    def get_data(self, time):
        return self.old_data


class LinearInterpolation(AAdapter):
    def __init__(self):
        super().__init__("LinearInterpolation")
        self.old_data = None
        self.new_data = None

    def set_data(self, data, time):
        self.old_data = self.new_data
        self.new_data = (time, data)

    def get_data(self, time):
        if self.old_data is None:
            return self.new_data[1]

        dt = (time - self.old_data[0]) / float(self.new_data[0] - self.old_data[0])
        return interpolate(self.old_data[1], self.new_data[1], dt)


class LinearIntegration(AAdapter):

    @classmethod
    def sum(cls):
        return LinearIntegration(normalize=False)

    @classmethod
    def mean(cls):
        return LinearIntegration(normalize=True)

    def __init__(self, normalize=True):
        super().__init__("LinearIntegration")
        self.data = []
        self.prev_time = 0
        self.normalize = normalize

    def set_data(self, data, time):
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

            v1 = interpolate(v_old, v_new, dt1)
            v2 = interpolate(v_old, v_new, dt2)

            sum_value += (dt2 - dt1) * scale * 0.5 * (v1 + v2)

        if self.normalize:
            dt = time - self.prev_time
            if dt > 0:
                sum_value /= dt

        if len(self.data) > 2:
            self.data = self.data[-2:]

        self.prev_time = time

        return sum_value


def interpolate(old_value, new_value, dt):
    return old_value + dt * (new_value - old_value)
