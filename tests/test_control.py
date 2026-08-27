import unittest

from backend.app.algorithms.control import ControlPolicy, MachineSnapshot, OxygenController


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.controller = OxygenController(ControlPolicy(minimum_runtime_seconds=300, minimum_stop_seconds=60, cooldown_seconds=30))

    def test_low_do_starts_machine(self):
        decision = self.controller.decide(MachineSnapshot(status="OFF"), 2.8, 100)
        self.assertEqual(decision.action, "START")

    def test_hysteresis_holds_between_thresholds(self):
        decision = self.controller.decide(MachineSnapshot(status="ON", last_transition_at=0), 4.0, 1000)
        self.assertEqual(decision.action, "NONE")

    def test_minimum_runtime_blocks_stop(self):
        decision = self.controller.decide(MachineSnapshot(status="ON", last_transition_at=900), 5.5, 1000)
        self.assertEqual(decision.reason, "minimum_runtime")

    def test_sensor_failure_stops_running_machine(self):
        decision = self.controller.decide(MachineSnapshot(status="ON", sensor_valid=False), None, 1000)
        self.assertEqual(decision.reason, "sensor_failure_protection")

    def test_manual_override_blocks_auto_start(self):
        decision = self.controller.decide(MachineSnapshot(manual_override=True), 2.0, 1000)
        self.assertEqual(decision.reason, "manual_mode")


if __name__ == "__main__":
    unittest.main()

