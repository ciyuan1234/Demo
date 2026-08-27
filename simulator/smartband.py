"""Smart-band HAL and MOCK alarm display implementation."""

from dataclasses import dataclass
from typing import Optional

from .mqtt import MQTTClient
from .topics import alarm_topic


class SmartBandInterface:
    def connect(self) -> bool:
        raise NotImplementedError

    def notify_alarm(self, message: str, level: str, do_value: Optional[float] = None) -> bool:
        raise NotImplementedError


@dataclass(frozen=True)
class BandEvent:
    event: str
    message: str
    level: str
    mode: str = "MOCK"


class MockSmartBand(SmartBandInterface):
    """MOCK BLE band; it does not connect to an ESP32 or real BLE device."""

    def __init__(self, band_id: str = "BAND_001"):
        self.band_id = band_id
        self.connected = False
        self.events: list[BandEvent] = []
        self.display_text = ""

    def connect(self) -> bool:
        self.connected = True
        self.events.append(BandEvent("BLE_CONNECTED", "BLE connected", "INFO"))
        return True

    def disconnect(self) -> None:
        self.connected = False
        self.events.append(BandEvent("BLE_DISCONNECTED", "BLE disconnected", "INFO"))

    def notify_alarm(self, message: str, level: str, do_value: Optional[float] = None) -> bool:
        if not self.connected:
            return False
        suffix = f" DO: {do_value:.1f} mg/L" if do_value is not None else ""
        self.display_text = f"{message}{suffix}"
        self.events.extend([
            BandEvent("ALARM", self.display_text, level),
            BandEvent("VIBRATE", "vibration", level),
            BandEvent("DISPLAY", self.display_text, level),
        ])
        return True


class MockSmartBandAlarmReceiver:
    def __init__(self, mqtt_client: MQTTClient, band: MockSmartBand, device_id: str):
        self.band = band
        mqtt_client.subscribe(alarm_topic(device_id), self.on_alarm)

    def on_alarm(self, topic: str, payload: dict) -> None:
        self.band.notify_alarm(payload.get("message", "Water quality alarm"), payload.get("level", "WARNING"), payload.get("do"))

