"""MQTT ingestion boundary.

The consumer accepts the same small interface as simulator.MockMQTTBroker.
A future Paho/Mosquitto adapter can call ``on_message`` with decoded JSON
without changing the telemetry service or database code.
"""

from typing import Iterable

from sqlalchemy.orm import Session

from ..schemas import TelemetryMessage
from ..services.telemetry import ingest_telemetry


class TelemetryConsumer:
    def __init__(self, mqtt_client, db_factory, device_ids: Iterable[str]):
        self.mqtt_client = mqtt_client
        self.db_factory = db_factory
        self.device_ids = list(device_ids)

    def start(self) -> None:
        for device_id in self.device_ids:
            self.mqtt_client.subscribe(f"aquaculture/device/{device_id}/telemetry", self.on_message)

    def on_message(self, topic: str, payload: dict) -> None:
        message = TelemetryMessage.model_validate(payload)
        db: Session = self.db_factory()
        try:
            ingest_telemetry(db, message, mqtt=self.mqtt_client)
        finally:
            db.close()
