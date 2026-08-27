"""Explainable, configurable first-stage water-quality rules."""

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class WaterQualityThresholds:
    do_critical: float = 3.0
    do_warning: float = 4.0
    do_recovery: float = 5.0
    ph_min: float = 6.5
    ph_max: float = 8.5
    turbidity_max: float = 100.0
    rapid_do_drop: float = 0.15


@dataclass(frozen=True)
class AlarmDecision:
    level: str
    message: str
    reason: str


def evaluate_water_quality(current, history: Sequence, thresholds: WaterQualityThresholds) -> AlarmDecision | None:
    if current.do < thresholds.do_critical:
        return AlarmDecision("CRITICAL", f"严重缺氧：DO {current.do:.2f} mg/L", "do_below_critical")
    if current.do < thresholds.do_warning:
        return AlarmDecision("WARNING", f"缺氧预警：DO {current.do:.2f} mg/L", "do_below_warning")
    if current.ph < thresholds.ph_min or current.ph > thresholds.ph_max:
        return AlarmDecision("WARNING", f"pH 异常：{current.ph:.2f}", "ph_out_of_range")
    if current.turbidity > thresholds.turbidity_max:
        return AlarmDecision("WARNING", f"浊度异常：{current.turbidity:.2f}", "turbidity_high")
    if history and current.do < history[-1].do - thresholds.rapid_do_drop:
        return AlarmDecision("WARNING", f"DO 快速下降：{current.do:.2f} mg/L", "do_drop_fast")
    return None


def risk_level(do_value: float, thresholds: WaterQualityThresholds) -> str:
    if do_value < thresholds.do_critical:
        return "CRITICAL"
    if do_value < thresholds.do_warning:
        return "WARNING"
    return "NORMAL"

