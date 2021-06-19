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
        value = self.old_data[1] + dt * (self.new_data[1] - self.old_data[1])
        return value
