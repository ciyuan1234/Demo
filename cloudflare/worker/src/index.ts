interface Env {
  DB: D1Database
  DO_CRITICAL_THRESHOLD?: string
  DO_WARNING_THRESHOLD?: string
  DO_START_THRESHOLD?: string
  DO_STOP_THRESHOLD?: string
  MINIMUM_RUNTIME_SECONDS?: string
  MINIMUM_STOP_TIME_SECONDS?: string
}

type ThresholdConfig = {
  doCritical: number
  doWarning: number
  doStart: number
  doStop: number
  minimumRuntimeSeconds: number
  minimumStopTimeSeconds: number
}

type Reading = {
  device_id: string
  pond_id: string
  timestamp: number
  temperature: number
  ph: number
  do: number
  turbidity: number
  data_source?: string
  mode?: string
  schema_version?: string
}

type Row = Record<string, unknown>

const json = (data: unknown, status = 200) => new Response(JSON.stringify(data), {
  status,
  headers: {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  },
})

const now = () => Math.floor(Date.now() / 1000)

const numberConfig = (value: string | undefined, fallback: number) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function thresholds(env: Env): ThresholdConfig {
  return {
    doCritical: numberConfig(env.DO_CRITICAL_THRESHOLD, 3),
    doWarning: numberConfig(env.DO_WARNING_THRESHOLD, 4),
    doStart: numberConfig(env.DO_START_THRESHOLD, 3),
    doStop: numberConfig(env.DO_STOP_THRESHOLD, 5),
    minimumRuntimeSeconds: numberConfig(env.MINIMUM_RUNTIME_SECONDS, 300),
    minimumStopTimeSeconds: numberConfig(env.MINIMUM_STOP_TIME_SECONDS, 60),
  }
}

function validReading(value: unknown): value is Reading {
  if (!value || typeof value !== 'object') return false
  const reading = value as Reading
  return typeof reading.device_id === 'string' && typeof reading.pond_id === 'string' &&
    Number.isInteger(reading.timestamp) &&
    [reading.temperature, reading.ph, reading.do, reading.turbidity].every(Number.isFinite) &&
    reading.temperature >= -10 && reading.temperature <= 60 &&
    reading.ph >= 0 && reading.ph <= 14 &&
    reading.do >= 0 && reading.do <= 20 &&
    reading.turbidity >= 0 && reading.turbidity <= 1000
}

async function evaluateAndStore(env: Env, reading: Reading): Promise<void> {
  const config = thresholds(env)
  const source = reading.data_source ?? 'simulated'
  const mode = reading.mode ?? 'MOCK'

  await env.DB.prepare(`INSERT INTO devices(device_id,pond_id,mode,status,last_seen)
    VALUES(?,?,?,'ONLINE',?)
    ON CONFLICT(device_id) DO UPDATE SET pond_id=excluded.pond_id,
    mode=excluded.mode,status='ONLINE',last_seen=excluded.last_seen`)
    .bind(reading.device_id, reading.pond_id, mode, reading.timestamp).run()

  await env.DB.prepare(`INSERT INTO sensor_data
    (device_id,pond_id,timestamp,temperature,ph,do,turbidity,data_source,mode,schema_version)
    VALUES(?,?,?,?,?,?,?,?,?,?)`)
    .bind(reading.device_id, reading.pond_id, reading.timestamp, reading.temperature,
      reading.ph, reading.do, reading.turbidity, source, mode, reading.schema_version ?? '1.0').run()

  let level = 'NORMAL'
  let reason = ''
  let message = ''
  if (reading.do < config.doCritical) {
    level = 'CRITICAL'
    reason = 'do_below_critical'
    message = `DO ${reading.do.toFixed(2)} mg/L - critical hypoxia risk`
  } else if (reading.do < config.doWarning) {
    level = 'WARNING'
    reason = 'do_below_warning'
    message = `DO ${reading.do.toFixed(2)} mg/L - hypoxia warning`
  }

  if (level !== 'NORMAL') {
    const active = await env.DB.prepare(`SELECT id FROM alarms
      WHERE pond_id=? AND level=? AND acknowledged=0 LIMIT 1`).bind(reading.pond_id, level).first()
    if (!active) {
      await env.DB.prepare(`INSERT INTO alarms
        (device_id,pond_id,level,message,reason,created_at) VALUES(?,?,?,?,?,?)`)
        .bind(reading.device_id, reading.pond_id, level, message, reason, reading.timestamp).run()
    }
  }

  const history = await env.DB.prepare(`SELECT do,timestamp FROM sensor_data
    WHERE pond_id=? ORDER BY timestamp DESC LIMIT 60`).bind(reading.pond_id).all<Row>()
  const rows = history.results.reverse()
  const average = rows.length
    ? rows.reduce((sum, row) => sum + Number(row.do), 0) / rows.length
    : reading.do
  const first = rows[0]
  const elapsed = first ? (reading.timestamp - Number(first.timestamp)) / 60 : 0
  const rate = elapsed > 0 ? (reading.do - Number(first.do)) / elapsed : 0
  const projected = average + rate * 60
  const risk = projected < config.doCritical ? 'CRITICAL'
    : projected < config.doWarning ? 'WARNING' : 'NORMAL'
  const probability = risk === 'CRITICAL' ? 0.82 : risk === 'WARNING' ? 0.58 : 0.12

  await env.DB.prepare(`INSERT INTO predictions
    (pond_id,risk_level,probability,horizon_minutes,data_source,created_at)
    VALUES(?,?,?,?,?,?)`).bind(reading.pond_id, risk, probability, 60, source, reading.timestamp).run()
  await autoControl(env, reading, config)
}

async function autoControl(env: Env, reading: Reading, config: ThresholdConfig): Promise<void> {
  const machineId = `OXYGEN_${reading.pond_id.split('_').pop()}`
  await env.DB.prepare(`INSERT INTO oxygen_machines(machine_id,pond_id)
    VALUES(?,?) ON CONFLICT(machine_id) DO NOTHING`).bind(machineId, reading.pond_id).run()
  const machine = await env.DB.prepare(`SELECT * FROM oxygen_machines
    WHERE machine_id=?`).bind(machineId).first<Row>()
  if (!machine || machine.mode !== 'AUTO' || Number(machine.manual_override) || Number(machine.emergency_stop)) return

  const status = String(machine.status)
  const last = Number(machine.last_transition_at ?? 0)
  let action = ''
  let reason = ''
  if (status === 'OFF' && reading.do < config.doStart &&
      reading.timestamp - last >= config.minimumStopTimeSeconds) {
    action = 'START'
    reason = 'do_below_start_threshold'
  }
  if (status === 'ON' && reading.do > config.doStop &&
      reading.timestamp - last >= config.minimumRuntimeSeconds) {
    action = 'STOP'
    reason = 'do_above_stop_threshold'
  }
  if (!action) return

  const newStatus = action === 'START' ? 'ON' : 'OFF'
  await env.DB.prepare(`UPDATE oxygen_machines SET status=?,last_transition_at=?,
    last_command_at=? WHERE machine_id=?`).bind(newStatus, reading.timestamp,
    reading.timestamp, machineId).run()
  await env.DB.prepare(`INSERT INTO control_logs
    (machine_id,operator,action,reason,result,created_at) VALUES(?,?,?,?,?,?)`)
    .bind(machineId, 'system', action, reason, 'ACCEPTED', reading.timestamp).run()
  await env.DB.prepare(`UPDATE simulation_states SET oxygen_on=? WHERE pond_id=?`)
    .bind(action === 'START' ? 1 : 0, reading.pond_id).run()
}

async function simulate(env: Env): Promise<void> {
  for (let index = 1; index <= 3; index += 1) {
    const pondId = `POND_${String(index).padStart(3, '0')}`
    const deviceId = `NODE_${String(index).padStart(3, '0')}`
    let state = await env.DB.prepare(`SELECT * FROM simulation_states
      WHERE pond_id=?`).bind(pondId).first<Row>()
    if (!state) {
      await env.DB.prepare(`INSERT INTO simulation_states
        (pond_id,temperature,ph,do,turbidity) VALUES(?,27,7.3,5.8,12)`).bind(pondId).run()
      state = { temperature: 27, ph: 7.3, do: 5.8, turbidity: 12, tick: 0, oxygen_on: 0 }
    }

    const tick = Number(state.tick) + 1
    const oxygenOn = Number(state.oxygen_on) === 1
    const hypoxia = tick % 30 >= 10 && tick % 30 < 20
    const doValue = Math.max(0, Math.min(20, Number(state.do) +
      (oxygenOn ? 0.30 : hypoxia ? -0.22 : (5.8 - Number(state.do)) * 0.12)))
    const temperature = Number(state.temperature) + 0.01
    await env.DB.prepare(`UPDATE simulation_states SET temperature=?,do=?,tick=?
      WHERE pond_id=?`).bind(temperature, doValue, tick, pondId).run()
    await evaluateAndStore(env, {
      device_id: deviceId, pond_id: pondId, timestamp: now(), temperature,
      ph: Number(state.ph), do: doValue, turbidity: Number(state.turbidity),
      data_source: 'simulated', mode: 'MOCK', schema_version: '1.0',
    })
  }
}

async function handle(request: Request, env: Env): Promise<Response> {
  if (request.method === 'OPTIONS') return json(null, 204)
  const url = new URL(request.url)
  const path = url.pathname

  if (path === '/health') return json({ status: 'ok', mode: 'MOCK_CLOUDFLARE_WORKER' })
  if (path === '/api/internal/telemetry' && request.method === 'POST') {
    const body = await request.json()
    if (!validReading(body)) return json({ detail: 'invalid telemetry' }, 422)
    await evaluateAndStore(env, body)
    return json({ accepted: true, data_source: body.data_source ?? 'simulated', mode: body.mode ?? 'MOCK' }, 201)
  }
  if (path === '/api/devices') return json((await env.DB.prepare(
    `SELECT device_id,pond_id,mode,status FROM devices ORDER BY device_id`).all()).results)

  const deviceMatch = path.match(/^\/api\/devices\/([^/]+)$/)
  if (deviceMatch) {
    const row = await env.DB.prepare(`SELECT device_id,pond_id,mode,status FROM devices
      WHERE device_id=?`).bind(deviceMatch[1]).first()
    return row ? json(row) : json({ detail: 'device not found' }, 404)
  }
  if (path === '/api/water-quality/latest') {
    const pond = url.searchParams.get('pond_id')
    const query = pond ? `SELECT * FROM sensor_data WHERE pond_id=? ORDER BY timestamp DESC LIMIT 1`
      : `SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1`
    const row = await env.DB.prepare(query).bind(...(pond ? [pond] : [])).first()
    return row ? json(row) : json({ detail: 'no water-quality data' }, 404)
  }
  if (path === '/api/water-quality/history') {
    const pond = url.searchParams.get('pond_id') ?? 'POND_001'
    const rows = await env.DB.prepare(`SELECT * FROM sensor_data WHERE pond_id=?
      ORDER BY timestamp DESC LIMIT 100`).bind(pond).all()
    return json(rows.results)
  }
  if (path === '/api/alarms') {
    const pond = url.searchParams.get('pond_id')
    const rows = pond ? await env.DB.prepare(`SELECT * FROM alarms WHERE pond_id=?
      ORDER BY created_at DESC LIMIT 100`).bind(pond).all()
      : await env.DB.prepare(`SELECT * FROM alarms ORDER BY created_at DESC LIMIT 100`).all()
    return json(rows.results)
  }
  if (path === '/api/predictions') {
    const pond = url.searchParams.get('pond_id')
    const rows = pond ? await env.DB.prepare(`SELECT * FROM predictions WHERE pond_id=?
      ORDER BY created_at DESC LIMIT 20`).bind(pond).all()
      : await env.DB.prepare(`SELECT * FROM predictions ORDER BY created_at DESC LIMIT 20`).all()
    return json(rows.results)
  }
  if (path === '/api/oxygen/status') {
    const machineId = url.searchParams.get('machine_id') ?? 'OXYGEN_001'
    const row = await env.DB.prepare(`SELECT * FROM oxygen_machines WHERE machine_id=?`).bind(machineId).first()
    return row ? json(row) : json({ detail: 'oxygen machine not found' }, 404)
  }

  const oxygenAction = path.match(/^\/api\/oxygen\/(start|stop)$/)?.[1]
  if (oxygenAction && request.method === 'POST') {
    const machineId = url.searchParams.get('machine_id') ?? 'OXYGEN_001'
    const pondId = url.searchParams.get('pond_id') ?? 'POND_001'
    const status = oxygenAction === 'start' ? 'ON' : 'OFF'
    const timestamp = now()
    await env.DB.prepare(`INSERT INTO oxygen_machines
      (machine_id,pond_id,status,mode,last_transition_at,last_command_at)
      VALUES(?,?,?,'MANUAL',?,?) ON CONFLICT(machine_id) DO UPDATE SET status=?,
      mode='MANUAL',last_transition_at=?,last_command_at=?`)
      .bind(machineId, pondId, status, timestamp, timestamp, status, timestamp, timestamp).run()
    await env.DB.prepare(`INSERT INTO control_logs
      (machine_id,operator,action,reason,result,created_at) VALUES(?,?,?,?,?,?)`)
      .bind(machineId, 'web_user', oxygenAction.toUpperCase(), `manual_${oxygenAction}`,
        'ACCEPTED', timestamp).run()
    return json({ machine_id: machineId, status, mode: 'MANUAL' })
  }
  if (path === '/api/oxygen/mode' && request.method === 'POST') {
    const mode = url.searchParams.get('mode')
    if (mode !== 'AUTO' && mode !== 'MANUAL') return json({ detail: 'mode must be AUTO or MANUAL' }, 400)
    const machineId = url.searchParams.get('machine_id') ?? 'OXYGEN_001'
    const pondId = url.searchParams.get('pond_id') ?? 'POND_001'
    await env.DB.prepare(`INSERT INTO oxygen_machines(machine_id,pond_id,mode)
      VALUES(?,?,?) ON CONFLICT(machine_id) DO UPDATE SET mode=?`)
      .bind(machineId, pondId, mode, mode).run()
    return json({ machine_id: machineId, mode })
  }
  return json({ detail: 'not found' }, 404)
}

export default {
  fetch: handle,
  scheduled: (_event: ScheduledEvent, env: Env, ctx: ExecutionContext) => ctx.waitUntil(simulate(env)),
}
