import unittest

from backend.app.algorithms.control import ControlPolicy
from simulator.closed_loop import MockClosedLoop
from simulator.environment import EnvironmentScenario, PondEnvironment, PondState


class ClosedLoopTests(unittest.TestCase):
    def test_hypoxia_starts_and_recovery_stops_machine(self):
        environment = PondEnvironment(PondState("POND_001", do=3.2), EnvironmentScenario.HYPOXIA)
        loop = MockClosedLoop(environment, policy=ControlPolicy(minimum_runtime_seconds=300, minimum_stop_seconds=0))
        events = [loop.step() for _ in range(12)]
        self.assertIn("START", [event.action for event in events])
        self.assertIn("STOP", [event.action for event in events])
        self.assertEqual(loop.machine.status().value, "OFF")

    def test_invalid_sensor_protects_running_machine(self):
        environment = PondEnvironment(PondState("POND_001", do=2.5), EnvironmentScenario.HYPOXIA)
        loop = MockClosedLoop(environment, policy=ControlPolicy(minimum_runtime_seconds=0, minimum_stop_seconds=0))
        loop.step()
        event = loop.step("out_of_range")
        self.assertFalse(event.sensor_valid)
        self.assertEqual(event.action, "STOP")


if __name__ == "__main__":
    unittest.main()

