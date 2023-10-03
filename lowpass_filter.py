import math


class LowPassFilter:
    def __init__(self, dt: float, y_old: float = 0):
        self.dt = dt
        self.y_old = y_old

    def filter(self, x_new, cutoff=20):
        alpha = self.dt / (self.dt + 1 / (2 * math.pi * cutoff))
        self.y_old = x_new * alpha + (1 - alpha) * self.y_old
        return self.y_old
