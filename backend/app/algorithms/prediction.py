"""Explainable first-stage DO trend prediction; no deep learning involved."""

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class PredictionResult:
    risk_level: str
    probability: float
    horizon_minutes: int
    moving_average: float
    do_rate_per_minute: float
    data_source: str = "simulated"


def moving_average(values: Sequence[float], window: int = 5) -> float:
    if not values:
        raise ValueError("at least one value is required")
    selected = values[-window:]
    return sum(selected) / len(selected)


def do_rate_per_minute(readings: Sequence) -> float:
    if len(readings) < 2:
        return 0.0
    first, last = readings[0], readings[-1]
    elapsed = (last.timestamp - first.timestamp) / 60.0
    return 0.0 if elapsed <= 0 else (last.do - first.do) / elapsed


def predict_do_risk(readings: Sequence, horizon_minutes: int = 60, critical_do: float = 3.0,
                    warning_do: float = 4.0) -> PredictionResult:
    if not readings:
        raise ValueError("at least one reading is required")
    average = moving_average([item.do for item in readings])
    rate = do_rate_per_minute(readings)
    projected = average + rate * horizon_minutes
    if projected < critical_do:
        risk, probability = "CRITICAL", min(0.99, max(0.5, (critical_do - projected) / critical_do + 0.5))
    elif projected < warning_do:
        risk, probability = "WARNING", min(0.89, max(0.35, (warning_do - projected) / warning_do + 0.25))
    else:
        risk, probability = "NORMAL", max(0.05, min(0.25, 0.15 - rate * 0.5))
    return PredictionResult(risk, round(probability, 4), horizon_minutes, round(average, 4), round(rate, 6))

