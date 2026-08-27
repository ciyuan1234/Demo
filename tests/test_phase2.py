import unittest

from simulator.device import MockIoTDevice
from simulator.environment import EnvironmentScenario, PondEnvironment, PondState
from simulator.lora import MockLoRaTransport
from simulator.mqtt import MockMQTTBroker
from simulator.sensors import MockWaterQualitySensor, SensorFault
from simulator.topics import status_topic, telemetry_topic


class Phase2Tests(unittest.TestCase):
    def make_device(self, lora=None):
        env = PondEnvironment(PondState("POND_001"), EnvironmentScenario.NORMAL)
        broker = MockMQTTBroker()
        device = MockIoTDevice("NODE_001", env, MockWaterQualitySensor("NODE_001", "POND_001"),
                               lora or MockLoRaTransport(), broker)
        return device, broker

    def test_sensor_to_lora_to_mqtt(self):
        device, broker = self.make_device()
        received = []
        broker.subscribe(telemetry_topic("NODE_001"), lambda topic, payload: received.append(payload))
        self.assertTrue(device.collect_and_transmit(100))
        self.assertIsNotNone(device.forward_received_packet())
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["data_source"], "simulated")

    def test_disconnected_sensor_publishes_status(self):
        device, broker = self.make_device()
        self.assertFalse(device.collect_and_transmit(100, SensorFault.DISCONNECTED))
        self.assertEqual(broker.messages[-1][0], status_topic("NODE_001"))

    def test_lora_loss_can_fail_transmission(self):
        device, _ = self.make_device(MockLoRaTransport(loss_rate=1.0, seed=1, max_retries=2))
        self.assertFalse(device.collect_and_transmit(100))


if __name__ == "__main__":
    unittest.main()

