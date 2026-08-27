"""Small CLI demo for the Phase 1 simulator."""

from .environment import EnvironmentScenario, PondEnvironment, PondState
from .sensors import MockWaterQualitySensor


def run_demo() -> None:
    pond = PondEnvironment(PondState("POND_001"))
    sensor = MockWaterQualitySensor("NODE_001", "POND_001")
    for timestamp in range(6):
        if timestamp == 2:
            pond.set_scenario(EnvironmentScenario.HYPOXIA)
        if timestamp == 4:
            pond.set_scenario(EnvironmentScenario.AERATION)
            pond.set_oxygen_machine("ON")
        print(sensor.read(pond.step(), timestamp).to_dict())


if __name__ == "__main__":
    run_demo()

