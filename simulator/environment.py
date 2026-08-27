"""Deterministic pond environment model.

The model is intentionally simple and explainable. It is a test fixture for
the software system, not a claim about a particular real pond.
"""

from dataclasses import dataclass
from enum import Enum


class EnvironmentScenario(str, Enum):
    NORMAL = "normal"
    HYPOXIA = "hypoxia"
    AERATION = "aeration"
    RECOVERY = "recovery"


@dataclass
class PondState:
    pond_id: str
    temperature: float = 27.0
    ph: float = 7.3
    do: float = 5.8
    turbidity: float = 12.0
    oxygen_machine_status: str = "OFF"


class PondEnvironment:
    """A pond with scenario-driven water-quality dynamics.

    ``step`` advances one simulation interval. Values are bounded to physical
    simulator limits, while sensor faults are applied later by Mock sensors.
    """

    def __init__(self, state: PondState, scenario: EnvironmentScenario = EnvironmentScenario.NORMAL):
        self.state = state
        self.scenario = scenario
        self._tick = 0

    def set_scenario(self, scenario: EnvironmentScenario) -> None:
        self.scenario = scenario

    def set_oxygen_machine(self, status: str) -> None:
        if status not in {"ON", "OFF", "FAULT"}:
            raise ValueError("oxygen machine status must be ON, OFF, or FAULT")
        self.state.oxygen_machine_status = status

    def step(self) -> PondState:
        self._tick += 1
        s = self.state
        if self.scenario is EnvironmentScenario.NORMAL:
            s.temperature += 0.01
            s.ph += (7.3 - s.ph) * 0.08
            s.do += (5.8 - s.do) * 0.12
            s.turbidity += (12.0 - s.turbidity) * 0.10
        elif self.scenario is EnvironmentScenario.HYPOXIA:
            s.temperature += 0.04
            s.ph -= 0.004
            s.do -= 0.22
            s.turbidity += 0.05
        elif self.scenario is EnvironmentScenario.AERATION:
            s.temperature += 0.01
            s.ph += (7.3 - s.ph) * 0.04
            s.do += 0.30 if s.oxygen_machine_status == "ON" else -0.03
            s.turbidity += (12.0 - s.turbidity) * 0.04
        elif self.scenario is EnvironmentScenario.RECOVERY:
            s.temperature += (27.0 - s.temperature) * 0.02
            s.ph += (7.3 - s.ph) * 0.10
            s.do += (6.0 - s.do) * (0.18 if s.oxygen_machine_status == "ON" else 0.04)
            s.turbidity += (12.0 - s.turbidity) * 0.12
        else:  # pragma: no cover - Enum prevents this in normal use.
            raise ValueError(f"unsupported scenario: {self.scenario}")

        s.temperature = max(0.0, min(45.0, s.temperature))
        s.ph = max(0.0, min(14.0, s.ph))
        s.do = max(0.0, min(20.0, s.do))
        s.turbidity = max(0.0, min(1000.0, s.turbidity))
        return s

