"""Mock IoT node: sensor -> LoRa -> gateway -> MQTT."""

from typing import Optional

from .environment import PondEnvironment
from .lora import LoRaTransport
from .mqtt import MQTTClient
from .sensors import MockWaterQualitySensor, validate_reading
from .topics import status_topic, telemetry_topic


class MockIoTDevice:
    """MOCK STM32/LoRa node with the same message boundary planned for REAL hardware."""

    def __init__(self, device_id: str, environment: PondEnvironment, sensor: MockWaterQualitySensor,
                 lora: LoRaTransport, mqtt: MQTTClient):
        self.device_id = device_id
        self.environment = environment
        self.sensor = sensor
        self.lora = lora
        self.mqtt = mqtt

    def collect_and_transmit(self, timestamp: int, fault: str = "none") -> bool:
        reading = self.sensor.read(self.environment.step(), timestamp, fault)
        if reading is None:
            self.mqtt.publish(status_topic(self.device_id), {"device_id": self.device_id, "status": "SENSOR_DISCONNECTED", "mode": "MOCK"})
            return False
        validation = validate_reading(reading)
        if not validation.valid:
            self.mqtt.publish(status_topic(self.device_id), {"device_id": self.device_id, "status": "INVALID_SENSOR_DATA", "reason": validation.reason, "mode": "MOCK"})
            return False
        return self.lora.send(reading.to_dict())

    def forward_received_packet(self) -> Optional[dict]:
        packet = self.lora.receive()
        if packet is None or packet.corrupted:
            return None
        import json
        payload = json.loads(packet.payload)
        self.mqtt.publish(telemetry_topic(self.device_id), payload)
        return payload

