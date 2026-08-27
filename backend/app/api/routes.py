from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Alarm, Device, OxygenMachine, Prediction, SensorData
from ..schemas import DeviceResponse, TelemetryMessage
from ..services.telemetry import ingest_telemetry
from ..services.oxygen import get_or_create_machine, record_control

router = APIRouter(prefix="/api")


@router.get("/devices", response_model=list[DeviceResponse])
def list_devices(db: Session = Depends(get_db)):
    return list(db.scalars(select(Device).order_by(Device.device_id)))


@router.get("/devices/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, db: Session = Depends(get_db)):
    device = db.scalar(select(Device).where(Device.device_id == device_id))
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")
    return device


@router.get("/water-quality/latest")
def latest_water_quality(pond_id: str | None = Query(default=None), db: Session = Depends(get_db)):
    query = select(SensorData).order_by(desc(SensorData.timestamp)).limit(1)
    if pond_id:
        query = query.where(SensorData.pond_id == pond_id)
    row = db.scalar(query)
    if row is None:
        raise HTTPException(status_code=404, detail="no water-quality data")
    return row


@router.get("/water-quality/history")
def water_quality_history(pond_id: str, limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)):
    query = select(SensorData).where(SensorData.pond_id == pond_id).order_by(desc(SensorData.timestamp)).limit(limit)
    return list(db.scalars(query))


@router.get("/alarms")
def list_alarms(pond_id: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)):
    query = select(Alarm).order_by(desc(Alarm.created_at)).limit(limit)
    if pond_id:
        query = query.where(Alarm.pond_id == pond_id)
    return list(db.scalars(query))


@router.get("/predictions")
def list_predictions(pond_id: str | None = Query(default=None), limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    query = select(Prediction).order_by(desc(Prediction.created_at)).limit(limit)
    if pond_id:
        query = query.where(Prediction.pond_id == pond_id)
    return list(db.scalars(query))


@router.get("/oxygen/status")
def oxygen_status(machine_id: str = "OXYGEN_001", db: Session = Depends(get_db)):
    machine = db.scalar(select(OxygenMachine).where(OxygenMachine.machine_id == machine_id))
    if machine is None:
        raise HTTPException(status_code=404, detail="oxygen machine not found")
    return machine


@router.post("/oxygen/start")
def oxygen_start(machine_id: str = "OXYGEN_001", pond_id: str = "POND_001", db: Session = Depends(get_db)):
    machine = get_or_create_machine(db, machine_id, pond_id)
    record_control(db, machine, "START", "manual_start", operator="web_user")
    return {"machine_id": machine.machine_id, "status": machine.status, "mode": machine.mode}


@router.post("/oxygen/stop")
def oxygen_stop(machine_id: str = "OXYGEN_001", pond_id: str = "POND_001", db: Session = Depends(get_db)):
    machine = get_or_create_machine(db, machine_id, pond_id)
    record_control(db, machine, "STOP", "manual_stop", operator="web_user")
    return {"machine_id": machine.machine_id, "status": machine.status, "mode": machine.mode}


@router.post("/oxygen/mode")
def oxygen_mode(mode: str, machine_id: str = "OXYGEN_001", pond_id: str = "POND_001", db: Session = Depends(get_db)):
    if mode not in {"AUTO", "MANUAL"}:
        raise HTTPException(status_code=400, detail="mode must be AUTO or MANUAL")
    machine = get_or_create_machine(db, machine_id, pond_id)
    machine.mode = mode
    db.commit()
    return {"machine_id": machine.machine_id, "status": machine.status, "mode": machine.mode}


@router.post("/internal/telemetry", status_code=201)
def ingest_internal_telemetry(message: TelemetryMessage, db: Session = Depends(get_db)):
    row = ingest_telemetry(db, message)
    return {"id": row.id, "accepted": True, "data_source": row.data_source, "mode": row.mode}
