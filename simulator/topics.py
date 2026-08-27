"""MQTT topic contract shared by simulator and backend."""


def telemetry_topic(device_id: str) -> str:
    return f"aquaculture/device/{device_id}/telemetry"


def status_topic(device_id: str) -> str:
    return f"aquaculture/device/{device_id}/status"


def alarm_topic(device_id: str) -> str:
    return f"aquaculture/device/{device_id}/alarm"


def command_topic(device_id: str) -> str:
    return f"aquaculture/device/{device_id}/command"


def ack_topic(device_id: str) -> str:
    return f"aquaculture/device/{device_id}/ack"

