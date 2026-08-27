import unittest

from simulator.environment import EnvironmentScenario, PondEnvironment, PondState
from simulator.schemas import WaterQualityReading
from simulator.sensors import MockWaterQualitySensor, SensorFault, validate_reading


class Phase1Tests(unittest.TestCase):
    def test_hypoxia_decreases_do(self):
        env = PondEnvironment(PondState("POND_001"), EnvironmentScenario.HYPOXIA)
        before = env.state.do
        for _ in range(5):
            env.step()
        self.assertLess(env.state.do, before)

    def test_aeration_recovers_do(self):
        env = PondEnvironment(PondState("POND_001", do=2.5), EnvironmentScenario.AERATION)
        env.set_oxygen_machine("ON")
        before = env.state.do
        for _ in range(5):
            env.step()
        self.assertGreater(env.state.do, before)

    def test_sensor_out_of_range_is_rejected(self):
        reading = WaterQualityReading("NODE_001", "POND_001", 1, 27.0, 7.3, 999.0, 12.0)
        result = validate_reading(reading)
        self.assertFalse(result.valid)
        self.assertEqual(result.reason, "do_out_of_range")

    def test_disconnected_sensor_returns_no_reading(self):
        sensor = MockWaterQualitySensor("NODE_001", "POND_001")
        self.assertIsNone(sensor.read(PondState("POND_001"), 1, SensorFault.DISCONNECTED))

    def test_reading_is_explicitly_simulated_mock(self):
        sensor = MockWaterQualitySensor("NODE_001", "POND_001")
        reading = sensor.read(PondState("POND_001"), 1)
        self.assertEqual(reading.data_source, "simulated")
        self.assertEqual(reading.mode, "MOCK")


if __name__ == "__main__":
    unittest.main()

