# AIoT 水产养殖智能水质监测原型

这是一个 **Hardware-independent First** 的数字原型。当前传感器、STM32、LoRa、增氧机和手环全部使用 `MOCK` 实现；业务层只依赖接口，未来可以替换为 `REAL` 适配器。

## 当前推荐：本地运行

需要 Node.js 20+。Cloudflare Worker 使用本地 Wrangler，数据库使用本地 D1；不需要服务器、域名或 Cloudflare 账号。

首次初始化本地 D1：

```powershell
cd cloudflare/worker
npm install
npx wrangler d1 migrations apply aquaculture-db --local
```

启动本地 API：

```powershell
npx wrangler dev --local --test-scheduled --port 8787
```

另开终端启动前端：

```powershell
cd frontend
npm install
npm run dev
```

访问：

- Dashboard：<http://127.0.0.1:5173>
- Worker API：<http://127.0.0.1:8787>
- 健康检查：<http://127.0.0.1:8787/health>
- 手动触发模拟采集：<http://127.0.0.1:8787/cdn-cgi/handler/scheduled>

每次触发模拟采集都会更新 `POND_001`、`POND_002`、`POND_003`，并执行规则预警、趋势预测和滞回增氧控制。

## Docker 本地完整架构

如果已安装 Docker Desktop，也可以运行原有 FastAPI、MySQL、Mosquitto 和模拟器架构：

```bash
docker compose up --build
```

访问：

- Dashboard：<http://localhost:8080>
- FastAPI 文档：<http://localhost:8000/docs>
- MQTT：`localhost:1883`

## Cloudflare 免费方案

Cloudflare 版本由 Pages（前端）+ Workers（API）+ D1（数据库）+ Cron（定时模拟采集）组成。Pages 和 Worker 是两个部署单元。

先在 Cloudflare 创建 D1 数据库：

```bash
cd cloudflare/worker
npx wrangler login
npx wrangler d1 create aquaculture-db
```

将命令输出的 `database_id` 写入 `cloudflare/worker/wrangler.jsonc` 的 `d1_databases[0]`，然后：

```bash
npx wrangler d1 migrations apply aquaculture-db --remote
npx wrangler deploy
```

前端部署到 Pages 时，构建命令为：

```bash
cd frontend && npm install && npm run build
```

输出目录为 `frontend/dist`。将 `VITE_API_BASE_URL` 设置为已部署 Worker 的 URL，例如 `https://aquaculture-api.<your-subdomain>.workers.dev`。

仓库中的 GitHub Actions 仅在配置 Cloudflare Secrets 后使用：

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_PAGES_PROJECT`
- Pages 构建变量 `VITE_API_BASE_URL`

## 数据流

```text
Mock Environment
  -> Mock Sensor
  -> Mock IoT Node
  -> Mock LoRa / MQTT
  -> FastAPI + MySQL（Docker 本地路径）
  -> Worker + D1（Cloudflare 路径）
  -> Alarm / Trend / Risk Prediction
  -> Auto Oxygen Control
  -> Mock Oxygen Machine / Mock Smart Band
  -> Dashboard
```

两条路径使用相同的遥测字段和 MQTT Topic 约定：

```text
aquaculture/device/{device_id}/telemetry
aquaculture/device/{device_id}/status
aquaculture/device/{device_id}/alarm
aquaculture/device/{device_id}/command
aquaculture/device/{device_id}/ack
```

模拟数据明确标记为：

```json
{
  "data_source": "simulated",
  "mode": "MOCK",
  "schema_version": "1.0"
}
```

## 测试

Python 测试：

```bash
python -m unittest discover -s tests -v
```

前端构建：

```bash
cd frontend
npm run build
```

Cloudflare Worker 类型检查：

```bash
cd cloudflare/worker
npx tsc --noEmit
```

## Mock / Real 替换边界

| 能力 | 当前实现 | 未来替换 |
|---|---|---|
| 水质传感器 | `MockWaterQualitySensor` | DS18B20 / pH / DO / turbidity adapter |
| LoRa | `MockLoRaTransport` | `SX1278LoRaTransport` |
| 增氧机 | `MockOxygenMachine` | Relay / contactor adapter |
| 手环 | `MockSmartBand` | ESP32-C3 BLE adapter |

任何真实硬件能力都不能直接进入业务层。
