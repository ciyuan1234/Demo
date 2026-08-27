"""REAL network adapter for Mosquitto, keeping the business layer unchanged."""

import json
import os
import threading
import time

import paho.mqtt.client as mqtt

from ..core.config import settings
from ..db import SessionLocal
from ..schemas import TelemetryMessage
from ..services.telemetry import ingest_telemetry


class MosquittoTelemetrySubscriber:
    """Connects to MQTT only; sensor and actuator hardware remain MOCK/REAL adapters."""

    def __init__(self):
        self.host = os.getenv("MQTT_HOST", "mosquitto")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if settings.mqtt_username:
            self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        if settings.mqtt_tls:
            self.client.tls_set()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def start(self) -> None:
        threading.Thread(target=self._connect_until_ready, daemon=True, name="mqtt-subscriber").start()

    def _connect_until_ready(self) -> None:
        while True:
            try:
                self.client.connect(self.host, self.port, 60)
                self.client.loop_start()
                return
            except OSError:
                time.sleep(2)

    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:
        if int(reason_code) == 0:
            client.subscribe("aquaculture/device/+/telemetry", qos=1)

    def _on_message(self, client, userdata, message) -> None:
        db = SessionLocal()
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            ingest_telemetry(db, TelemetryMessage.model_validate(payload), mqtt=self)
        except (ValueError, TypeError, json.JSONDecodeError):
            db.rollback()
        finally:
            db.close()

    def publish(self, topic: str, payload: dict) -> None:
        self.client.publish(topic, json.dumps(payload), qos=1)
