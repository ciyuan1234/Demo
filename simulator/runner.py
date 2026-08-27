"""Long-running MOCK telemetry publisher for Docker Compose."""

import json
import os
import time

import paho.mqtt.client as mqtt

from .environment import EnvironmentScenario, PondEnvironment, PondState
from .sensors import MockWaterQualitySensor
from .oxygen import MockOxygenMachine
from .topics import ack_topic, command_topic, status_topic, telemetry_topic


def run() -> None:
    host = os.getenv("MQTT_HOST", "mosquitto")
    port = int(os.getenv("MQTT_PORT", "1883"))
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    while True:
        try:
            client.connect(host, port, 60)
            break
        except OSError:
            time.sleep(2)
    client.loop_start()
    ponds = [PondEnvironment(PondState(f"POND_{index:03d}")) for index in range(1, 4)]
    sensors = [MockWaterQualitySensor(f"NODE_{index:03d}", pond.state.pond_id) for index, pond in enumerate(ponds, 1)]
    machines = [MockOxygenMachine() for _ in ponds]

    def on_command(client, userdata, message):
        payload = json.loads(message.payload.decode("utf-8"))
        index = int(payload["pond_id"].split("_")[-1]) - 1
        machine = machines[index]
        action = payload.get("action")
        success = machine.start() if action == "START" else machine.stop() if action == "STOP" else False
        ponds[index].set_oxygen_machine(machine.status().value)
        if action == "START":
            ponds[index].set_scenario(EnvironmentScenario.RECOVERY)
        client.publish(ack_topic(payload["device_id"]), json.dumps({"device_id": payload["device_id"], "action": action, "accepted": success, "mode": "MOCK"}))

    for index in range(1, 4):
        client.subscribe(command_topic(f"NODE_{index:03d}"), qos=1)
    client.on_message = on_command
    tick = 0
    while True:
        for index, (pond, sensor) in enumerate(zip(ponds, sensors), 1):
            if tick % 30 == 10:
                pond.set_scenario(EnvironmentScenario.HYPOXIA)
            reading = sensor.read(pond.step(), int(time.time()))
            if reading is not None:
                client.publish(telemetry_topic(f"NODE_{index:03d}"), json.dumps(reading.to_dict()))
            client.publish(status_topic(f"NODE_{index:03d}"), json.dumps({"device_id": f"NODE_{index:03d}", "status": "ONLINE", "mode": "MOCK"}))
        tick += 1
        time.sleep(float(os.getenv("SIMULATOR_INTERVAL", "5")))


if __name__ == "__main__":
    run()
