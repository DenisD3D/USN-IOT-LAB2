import os
from abc import ABC
from typing import Union

from lowpass_filter import LowPassFilter


def should_fake_sensor():
    return os.getenv("FAKE_SENSORS", "False") == "True"


class Sensor(ABC):
    def __init__(self, name, low_pass_filter_interval=None):
        self.name = name
        self.low_pass_filter_interval = low_pass_filter_interval
        if self.low_pass_filter_interval is not None:
            self.low_pass_filter = LowPassFilter(dt=self.low_pass_filter_interval)

    def get_name(self):
        return self.name

    def get_value(self):
        pass

    def get_filtered_value(self):
        if self.low_pass_filter_interval is not None:
            value = self.get_value()
            if value is None:
                return None
            return self.low_pass_filter.filter(value)
        else:
            return self.get_value()


class AM2320Humidity(Sensor):
    def __init__(self, low_pass_filter_interval=None):
        super().__init__("AM2320 Humidity", low_pass_filter_interval)
        if not should_fake_sensor():
            import board
            import adafruit_am2320
            self.i2c = board.I2C()
            self.sensor = adafruit_am2320.AM2320(self.i2c)

    def get_value(self):
        try:
            return self.sensor.relative_humidity if not should_fake_sensor() else 0
        except OSError:
            return None
        except RuntimeError:
            return None


class AM2320Temperature(Sensor):
    def __init__(self, low_pass_filter_interval=None):
        super().__init__("AM2320 Temperature", low_pass_filter_interval)
        if not should_fake_sensor():
            import board
            import adafruit_am2320
            self.i2c = board.I2C()
            self.sensor = adafruit_am2320.AM2320(self.i2c)

    def get_value(self):
        try:
            return self.sensor.temperature if not should_fake_sensor() else 0
        except OSError:
            return None
        except RuntimeError:
            return None


class TMP36(Sensor):
    def __init__(self, low_pass_filter_interval=None):
        super().__init__("TMP36", low_pass_filter_interval)
        if not should_fake_sensor():
            from gpiozero import MCP3002
            self.adc = MCP3002(channel=0, differential=False)

    def get_value(self):
        try:
            return (self.adc.value * 3.3 - 0.5) * 100 if not should_fake_sensor() else 0
        except OSError:
            return None
        except RuntimeError:
            return None
