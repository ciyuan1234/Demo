from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..algorithms.rules import WaterQualityThresholds, evaluate_water_quality
from ..models import Alarm, SensorData


def check_and_create_alarm(db: Session, row: SensorData, thresholds: WaterQualityThresholds, mqtt=None) -> Alarm | None:
    history = list(db.scalars(select(SensorData).where(
        SensorData.pond_id == row.pond_id,
        SensorData.id != row.id,
    ).order_by(desc(SensorData.timestamp)).limit(5)))
    decision = evaluate_water_quality(row, list(reversed(history)), thresholds)
    if decision is None:
        return None
    recent = db.scalar(select(Alarm).where(
        Alarm.pond_id == row.pond_id,
        Alarm.level == decision.level,
        Alarm.acknowledged.is_(False),
    ).order_by(desc(Alarm.created_at)).limit(1))
    if recent is not None:
        return recent
    alarm = Alarm(device_id=row.device_id, pond_id=row.pond_id, level=decision.level,
                  message=decision.message, created_at=datetime.utcnow())
    db.add(alarm)
    db.flush()
    if mqtt is not None:
        mqtt.publish(f"aquaculture/device/{row.device_id}/alarm", {
            "device_id": row.device_id, "pond_id": row.pond_id, "level": decision.level,
            "message": decision.message, "reason": decision.reason, "do": row.do, "mode": row.mode,
        })
    return alarm
