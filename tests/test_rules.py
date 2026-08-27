import unittest

from backend.app.algorithms.rules import WaterQualityThresholds, evaluate_water_quality, risk_level


class RuleTests(unittest.TestCase):
    thresholds = WaterQualityThresholds()

    def reading(self, do, ph=7.3, turbidity=10.0):
        return type("Reading", (), {"do": do, "ph": ph, "turbidity": turbidity})()

    def test_do_levels(self):
        self.assertEqual(risk_level(2.9, self.thresholds), "CRITICAL")
        self.assertEqual(risk_level(3.5, self.thresholds), "WARNING")
        self.assertEqual(risk_level(5.0, self.thresholds), "NORMAL")

    def test_fast_do_drop(self):
        decision = evaluate_water_quality(self.reading(4.6), [self.reading(4.9)], self.thresholds)
        self.assertEqual(decision.reason, "do_drop_fast")

    def test_normal_has_no_alarm(self):
        self.assertIsNone(evaluate_water_quality(self.reading(5.5), [], self.thresholds))


if __name__ == "__main__":
    unittest.main()

