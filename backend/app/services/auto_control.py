"""Automatic control orchestration; hardware remains behind MQTT/actuator adapters."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..algorithms.control import ControlPolicy, MachineSnapshot, OxygenController
from ..models import ControlLog, OxygenMachine, SensorData


def evaluate_auto_control(db: Session, row: SensorData, mqtt=None, policy: ControlPolicy | None = None) -> str:
    machine_id = f"OXYGEN_{row.pond_id.split('_')[-1]}"
    machine = db.scalar(select(OxygenMachine).where(OxygenMachine.machine_id == machine_id))
    if machine is None:
        machine = OxygenMachine(machine_id=machine_id, pond_id=row.pond_id, status="OFF", mode="AUTO")
        db.add(machine)
        db.flush()
    snapshot = MachineSnapshot(status=machine.status, mode=machine.mode,
                               last_transition_at=machine.last_transition_at,
                               last_command_at=machine.last_command_at,
                               manual_override=machine.manual_override,
                               emergency_stop=machine.emergency_stop, sensor_valid=True)
    decision = OxygenController(policy or ControlPolicy()).decide(snapshot, row.do, row.timestamp)
    if decision.action == "NONE":
        return decision.reason
    machine.status = "ON" if decision.action == "START" else "OFF"
    machine.last_transition_at = row.timestamp
    machine.last_command_at = row.timestamp
    db.add(ControlLog(machine_id=machine.machine_id, operator="system", action=decision.action,
                      reason=decision.reason, result="ACCEPTED"))
    db.commit()
    if mqtt is not None:
        mqtt.publish(f"aquaculture/device/{row.device_id}/command", {
            "device_id": row.device_id, "pond_id": row.pond_id,
            "machine_id": machine.machine_id, "action": decision.action,
            "reason": decision.reason, "timestamp": row.timestamp, "mode": row.mode,
        })
    return decision.reason

