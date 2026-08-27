"""Mock sensor adapters and validation for the common device boundary."""

from dataclasses import dataclass
import random
from typing import Optional

from .environment import PondState
from .schemas import WaterQualityReading


class SensorFault(str):
    NONE = "none"
    DISCONNECTED = "disconnected"
    OUT_OF_RANGE = "out_of_range"
    FROZEN = "frozen"
    NOISY = "noisy"
    CORRUPTED = "corrupted"


@dataclass
class SensorValidation:
    valid: bool
    reason: Optional[str] = None


def validate_reading(reading: WaterQualityReading) -> SensorValidation:
    ranges = {
        "temperature": (-10.0, 60.0),
        "ph": (0.0, 14.0),
        "do": (0.0, 20.0),
        "turbidity": (0.0, 1000.0),
    }
    for field, (low, high) in ranges.items():
        value = getattr(reading, field)
        if not isinstance(value, (int, float)) or not low <= value <= high:
            return SensorValidation(False, f"{field}_out_of_range")
    return SensorValidation(True)


class MockWaterQualitySensor:
    """MOCK implementation; it never accesses GPIO, ADC, UART, or a sensor."""

    def __init__(self, device_id: str, pond_id: str, seed: int = 7):
        self.device_id = device_id
        self.pond_id = pond_id
        self._random = random.Random(seed)
        self._frozen: Optional[WaterQualityReading] = None

    def read(self, state: PondState, timestamp: int, fault: str = SensorFault.NONE) -> Optional[WaterQualityReading]:
        if fault == SensorFault.DISCONNECTED:
            return None
        values = {"temperature": state.temperature, "ph": state.ph, "do": state.do, "turbidity": state.turbidity}
        if fault == SensorFault.OUT_OF_RANGE:
            values["do"] = 999.0
        elif fault == SensorFault.NOISY:
            values = {key: value + self._random.uniform(-0.5, 0.5) for key, value in values.items()}
        reading = WaterQualityReading(self.device_id, self.pond_id, timestamp, **values)
        if fault == SensorFault.FROZEN:
            if self._frozen is None:
                self._frozen = reading
            return self._frozen
        if fault != SensorFault.FROZEN:
            self._frozen = None
        return reading

