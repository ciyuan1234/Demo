# 基于 AIoT 的水产养殖智能水质监测原型

这是一个 Hardware-independent First 的数字原型。当前所有传感器、STM32、LoRa、增氧机和智能手环均使用 `MOCK` 实现；代码不会把模拟数据或模拟设备伪装成真实硬件。

## 启动

需要 Docker Desktop：

```bash
docker compose up --build
```

访问：

- Dashboard：http://localhost:8080
- FastAPI：http://localhost:8000/docs
- MQTT：localhost:1883

## 当前数据流

```text
Mock Environment
  -> Mock Sensor
  -> Mock IoT Node
  -> Mosquitto MQTT
  -> FastAPI MQTT Consumer
  -> MySQL
  -> Alarm / Trend Prediction / Auto Control
  -> MQTT command
  -> Mock Oxygen Machine
  -> Environment Feedback
```

## Mock / Real 边界

| 能力 | 当前实现 | 未来替换 |
|---|---|---|
| 水质传感器 | `MockWaterQualitySensor` | DS18B20 / pH / DO / turbidity adapter |
| LoRa | `MockLoRaTransport` | `SX1278LoRaTransport` |
| 氧机 | `MockOxygenMachine` | Relay / contactor adapter |
| 手环 | `MockSmartBand` | ESP32-C3 BLE adapter |
| MQTT | Mosquitto + Paho | 保持协议不变 |

## MQTT Topic

```text
aquaculture/device/{device_id}/telemetry
aquaculture/device/{device_id}/status
aquaculture/device/{device_id}/alarm
aquaculture/device/{device_id}/command
aquaculture/device/{device_id}/ack
```

## 数据真实性标识

模拟器消息包含：

```json
{
  "data_source": "simulated",
  "mode": "MOCK",
  "schema_version": "1.0"
}
```

## 测试

Python 测试命令：

```bash
python -m unittest discover -s tests -v
```

测试覆盖环境变化、传感器校验、LoRa/MQTT、预警、预测、滞回控制、闭环和手环通知。

当前开发环境没有可执行 Python 解释器，因此本地测试尚未实际运行；Docker 构建会在容器中安装所需依赖。

