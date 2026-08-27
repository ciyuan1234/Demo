import unittest

from backend.app.algorithms.control import ControlPolicy, MachineSnapshot, OxygenController


class AutoControlTests(unittest.TestCase):
    def test_low_do_produces_start_command(self):
        decision = OxygenController(ControlPolicy()).decide(MachineSnapshot(status="OFF"), 2.5, 1000)
        self.assertEqual(decision.action, "START")

    def test_recovery_requires_minimum_runtime(self):
        decision = OxygenController(ControlPolicy()).decide(MachineSnapshot(status="ON", last_transition_at=1000), 5.8, 1100)
        self.assertEqual(decision.reason, "minimum_runtime")


if __name__ == "__main__":
    unittest.main()

