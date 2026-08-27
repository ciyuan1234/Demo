from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Device, DeviceStatus, SensorData
from ..schemas import TelemetryMessage
from ..algorithms.rules import WaterQualityThresholds
from ..core.config import settings
from .alarms import check_and_create_alarm
from .predictions import create_prediction
from .auto_control import evaluate_auto_control


def ingest_telemetry(db: Session, message: TelemetryMessage, mqtt=None) -> SensorData:
    device = db.scalar(select(Device).where(Device.device_id == message.device_id))
    if device is None:
        device = Device(device_id=message.device_id, pond_id=message.pond_id, mode=message.mode)
        db.add(device)
    device.status = "ONLINE"
    device.last_seen = datetime.utcnow()
    row = SensorData(**message.model_dump())
    db.add(row)
    db.flush()
    check_and_create_alarm(db, row, WaterQualityThresholds(
        do_critical=settings.do_critical, do_warning=settings.do_warning,
        do_recovery=settings.do_recovery, ph_min=settings.ph_min,
        ph_max=settings.ph_max, turbidity_max=settings.turbidity_max,
        rapid_do_drop=settings.rapid_do_drop,
    ), mqtt=mqtt)
    create_prediction(db, row)
    evaluate_auto_control(db, row, mqtt=mqtt)
    status = db.scalar(select(DeviceStatus).where(DeviceStatus.device_id == message.device_id))
    if status is None:
        db.add(DeviceStatus(device_id=message.device_id, status="ONLINE"))
    else:
        status.status = "ONLINE"
        status.reason = None
    db.commit()
    db.refresh(row)
    return row
