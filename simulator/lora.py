"""LoRa transport abstraction and deterministic MOCK implementation."""

from dataclasses import dataclass
import json
import random
from typing import Any, Dict, Optional


@dataclass
class LoRaPacket:
    payload: str
    attempt: int = 1
    duplicate: bool = False
    corrupted: bool = False


class LoRaTransport:
    """Interface boundary for future SX1278 adapter implementations."""

    def send(self, payload: Dict[str, Any]) -> bool:
        raise NotImplementedError

    def receive(self) -> Optional[LoRaPacket]:
        raise NotImplementedError


class MockLoRaTransport(LoRaTransport):
    """MOCK LoRa link: loss, delay, duplication and corruption are injectable."""

    def __init__(self, loss_rate: float = 0.0, delay_ticks: int = 0, duplicate_rate: float = 0.0,
                 corruption_rate: float = 0.0, seed: int = 11, max_retries: int = 3):
        for name, value in (("loss_rate", loss_rate), ("duplicate_rate", duplicate_rate), ("corruption_rate", corruption_rate)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        self.loss_rate = loss_rate
        self.delay_ticks = max(0, delay_ticks)
        self.duplicate_rate = duplicate_rate
        self.corruption_rate = corruption_rate
        self.max_retries = max(1, max_retries)
        self._random = random.Random(seed)
        self._queue: list[tuple[int, LoRaPacket]] = []
        self._tick = 0

    def send(self, payload: Dict[str, Any]) -> bool:
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        for attempt in range(1, self.max_retries + 1):
            if self._random.random() < self.loss_rate:
                continue
            corrupted = self._random.random() < self.corruption_rate
            packet = LoRaPacket(encoded if not corrupted else encoded[:-1] + "!", attempt, False, corrupted)
            self._queue.append((self._tick + self.delay_ticks, packet))
            if self._random.random() < self.duplicate_rate:
                self._queue.append((self._tick + self.delay_ticks, LoRaPacket(packet.payload, attempt, True, corrupted)))
            return True
        return False

    def receive(self) -> Optional[LoRaPacket]:
        for index, (ready_at, packet) in enumerate(self._queue):
            if ready_at <= self._tick:
                self._queue.pop(index)
                return packet
        self._tick += 1
        return None

    def acknowledge(self, packet: LoRaPacket) -> Dict[str, Any]:
        return {"type": "ACK", "attempt": packet.attempt, "mode": "MOCK", "duplicate": packet.duplicate}

