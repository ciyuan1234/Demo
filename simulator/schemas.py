"""Schemas shared by simulation and future real-device adapters."""

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class WaterQualityReading:
    device_id: str
    pond_id: str
    timestamp: int
    temperature: float
    ph: float
    do: float
    turbidity: float
    data_source: str = "simulated"
    mode: str = "MOCK"
    schema_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

