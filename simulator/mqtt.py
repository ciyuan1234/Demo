"""MQTT abstraction with an in-memory MOCK broker for local tests."""

import json
from dataclasses import dataclass
from typing import Callable, Dict, List


MessageHandler = Callable[[str, Dict], None]


class MQTTClient:
    """Interface boundary for a future Mosquitto/Paho adapter."""

    def publish(self, topic: str, payload: Dict) -> None:
        raise NotImplementedError

    def subscribe(self, topic: str, handler: MessageHandler) -> None:
        raise NotImplementedError


@dataclass
class MockMQTTBroker(MQTTClient):
    """Synchronous MOCK broker; payloads cross the boundary as JSON."""

    subscriptions: Dict[str, List[MessageHandler]] = None
    messages: List[tuple[str, str]] = None

    def __post_init__(self) -> None:
        self.subscriptions = self.subscriptions or {}
        self.messages = self.messages or []

    def publish(self, topic: str, payload: Dict) -> None:
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        self.messages.append((topic, encoded))
        for handler in self.subscriptions.get(topic, []):
            handler(topic, json.loads(encoded))

    def subscribe(self, topic: str, handler: MessageHandler) -> None:
        self.subscriptions.setdefault(topic, []).append(handler)

