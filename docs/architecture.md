# Architecture Notes

## Responsibilities

- `simulator/environment.py`: explainable pond dynamics.
- `simulator/sensors.py`: MOCK sensor output and validation boundary.
- `simulator/lora.py`: MOCK transport behavior.
- `simulator/runner.py`: long-running MQTT telemetry publisher and command receiver.
- `backend/app/algorithms`: pure rules, prediction, and control logic.
- `backend/app/services`: persistence and orchestration.
- `backend/app/mqtt`: MQTT adapters and consumers.
- `frontend/src`: API-driven dashboard; it does not generate fallback water-quality values.

## Control safety

Automatic control has separate start and stop thresholds. It also checks minimum runtime, minimum stop time, cooldown, sensor validity, manual mode, and emergency stop before issuing a command.

## Future hardware integration

Future adapters must implement the existing interfaces and preserve the telemetry and command schemas. Business rules, database models, API contracts, and dashboard code should not import STM32 GPIO, ADC, UART, SX1278, relay, or BLE libraries.

