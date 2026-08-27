import unittest

from simulator.mqtt import MockMQTTBroker
from simulator.smartband import MockSmartBand, MockSmartBandAlarmReceiver
from simulator.topics import alarm_topic


class SmartBandTests(unittest.TestCase):
    def test_alarm_reaches_connected_mock_band(self):
        broker = MockMQTTBroker()
        band = MockSmartBand()
        band.connect()
        MockSmartBandAlarmReceiver(broker, band, "NODE_001")
        broker.publish(alarm_topic("NODE_001"), {"message": "Severe hypoxia", "level": "CRITICAL", "do": 2.8})
        self.assertEqual([event.event for event in band.events[-3:]], ["ALARM", "VIBRATE", "DISPLAY"])
        self.assertIn("2.8 mg/L", band.display_text)

    def test_disconnected_band_does_not_claim_delivery(self):
        band = MockSmartBand()
        self.assertFalse(band.notify_alarm("test", "WARNING"))
        self.assertEqual(band.events, [])


if __name__ == "__main__":
    unittest.main()

