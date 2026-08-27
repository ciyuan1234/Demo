"""Pure automatic oxygen-control state machine."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ControlPolicy:
    start_do: float = 3.0
    stop_do: float = 5.0
    minimum_runtime_seconds: int = 300
    minimum_stop_seconds: int = 60
    cooldown_seconds: int = 30


@dataclass
class MachineSnapshot:
    status: str = "OFF"
    mode: str = "AUTO"
    last_transition_at: Optional[int] = None
    last_command_at: Optional[int] = None
    manual_override: bool = False
    emergency_stop: bool = False
    sensor_valid: bool = True


@dataclass(frozen=True)
class ControlDecision:
    action: str
    reason: str


class OxygenController:
    def __init__(self, policy: ControlPolicy = ControlPolicy()):
        self.policy = policy

    def decide(self, snapshot: MachineSnapshot, do_value: Optional[float], now: int) -> ControlDecision:
        if snapshot.emergency_stop:
            return ControlDecision("STOP", "emergency_stop") if snapshot.status == "ON" else ControlDecision("NONE", "emergency_stop")
        if snapshot.manual_override or snapshot.mode != "AUTO":
            return ControlDecision("NONE", "manual_mode")
        if not snapshot.sensor_valid or do_value is None:
            return ControlDecision("STOP", "sensor_failure_protection") if snapshot.status == "ON" else ControlDecision("NONE", "sensor_failure_protection")
        if snapshot.status == "OFF" and do_value < self.policy.start_do:
            if snapshot.last_transition_at is not None and now - snapshot.last_transition_at < self.policy.minimum_stop_seconds:
                return ControlDecision("NONE", "minimum_stop_time")
            if snapshot.last_command_at is not None and now - snapshot.last_command_at < self.policy.cooldown_seconds:
                return ControlDecision("NONE", "cooldown")
            return ControlDecision("START", "do_below_start_threshold")
        if snapshot.status == "ON" and do_value > self.policy.stop_do:
            if snapshot.last_transition_at is not None and now - snapshot.last_transition_at < self.policy.minimum_runtime_seconds:
                return ControlDecision("NONE", "minimum_runtime")
            return ControlDecision("STOP", "do_above_stop_threshold")
        return ControlDecision("NONE", "hysteresis_hold")

