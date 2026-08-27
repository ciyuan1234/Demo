import unittest

from backend.app.algorithms.prediction import do_rate_per_minute, moving_average, predict_do_risk


class PredictionTests(unittest.TestCase):
    def readings(self, values):
        return [type("Reading", (), {"do": value, "timestamp": index * 60})() for index, value in enumerate(values)]

    def test_moving_average(self):
        self.assertEqual(moving_average([1, 2, 3, 4, 5, 6], 3), 5.0)

    def test_declining_trend(self):
        readings = self.readings([5.8, 5.2, 4.6, 4.0, 3.4])
        self.assertLess(do_rate_per_minute(readings), 0)
        self.assertEqual(predict_do_risk(readings).risk_level, "CRITICAL")

    def test_stable_water_is_low_risk(self):
        result = predict_do_risk(self.readings([5.5, 5.5, 5.5]))
        self.assertEqual(result.risk_level, "NORMAL")
        self.assertEqual(result.data_source, "simulated")


if __name__ == "__main__":
    unittest.main()

