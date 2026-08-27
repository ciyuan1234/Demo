from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ControlLog, OxygenMachine


def get_or_create_machine(db: Session, machine_id: str, pond_id: str) -> OxygenMachine:
    machine = db.scalar(select(OxygenMachine).where(OxygenMachine.machine_id == machine_id))
    if machine is None:
        machine = OxygenMachine(machine_id=machine_id, pond_id=pond_id, status="OFF", mode="AUTO")
        db.add(machine)
        db.flush()
    return machine


def record_control(db: Session, machine: OxygenMachine, action: str, reason: str, operator: str = "system") -> ControlLog:
    if action not in {"START", "STOP", "NONE"}:
        raise ValueError("unsupported oxygen action")
    if action == "START":
        machine.status = "ON"
    elif action == "STOP":
        machine.status = "OFF"
    log = ControlLog(machine_id=machine.machine_id, operator=operator, action=action,
                     reason=reason, result="ACCEPTED", created_at=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(machine)
    return log

