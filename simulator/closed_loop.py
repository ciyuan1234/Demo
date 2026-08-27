"""Phase 5 end-to-end MOCK control loop."""

from dataclasses import dataclass

from backend.app.algorithms.control import ControlPolicy, MachineSnapshot, OxygenController

from .environment import EnvironmentScenario, PondEnvironment
from .oxygen import MockOxygenMachine
from .sensors import MockWaterQualitySensor, SensorFault, validate_reading


@dataclass(frozen=True)
class LoopEvent:
    timestamp: int
    do: float | None
    action: str
    reason: str
    oxygen_status: str
    sensor_valid: bool


class MockClosedLoop:
    """Connects MOCK environment, sensor, controller and oxygen machine only."""

    def __init__(self, environment: PondEnvironment, device_id: str = "NODE_001", step_seconds: int = 60,
                 policy: ControlPolicy | None = None):
        self.environment = environment
        self.sensor = MockWaterQualitySensor(device_id, environment.state.pond_id)
        self.machine = MockOxygenMachine()
        self.controller = OxygenController(policy or ControlPolicy())
        self.snapshot = MachineSnapshot()
        self.step_seconds = step_seconds
        self.now = 0

    def step(self, fault: str = SensorFault.NONE) -> LoopEvent:
        state = self.environment.step()
        reading = self.sensor.read(state, self.now, fault)
        valid = reading is not None and validate_reading(reading).valid
        decision = self.controller.decide(self.snapshot, reading.do if valid else None, self.now)
        if decision.action == "START" and self.machine.start():
            self.snapshot.status = "ON"
            self.snapshot.last_transition_at = self.now
            self.snapshot.last_command_at = self.now
            self.environment.set_oxygen_machine("ON")
            self.environment.set_scenario(EnvironmentScenario.RECOVERY)
        elif decision.action == "STOP" and self.machine.stop():
            self.snapshot.status = "OFF"
            self.snapshot.last_transition_at = self.now
            self.snapshot.last_command_at = self.now
            self.environment.set_oxygen_machine("OFF")
            self.environment.set_scenario(EnvironmentScenario.NORMAL)
        self.snapshot.sensor_valid = valid
        event = LoopEvent(self.now, reading.do if valid else None, decision.action, decision.reason,
                          self.machine.status().value, valid)
        self.now += self.step_seconds
        return event

