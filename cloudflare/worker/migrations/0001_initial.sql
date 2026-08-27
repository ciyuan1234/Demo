CREATE TABLE IF NOT EXISTS devices (
  device_id TEXT PRIMARY KEY, pond_id TEXT NOT NULL, mode TEXT NOT NULL DEFAULT 'MOCK',
  status TEXT NOT NULL DEFAULT 'OFFLINE', last_seen INTEGER
);
CREATE INDEX IF NOT EXISTS idx_devices_pond ON devices(pond_id);

CREATE TABLE IF NOT EXISTS sensor_data (
  id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT NOT NULL, pond_id TEXT NOT NULL,
  timestamp INTEGER NOT NULL, temperature REAL NOT NULL, ph REAL NOT NULL, do REAL NOT NULL,
  turbidity REAL NOT NULL, data_source TEXT NOT NULL DEFAULT 'simulated',
  mode TEXT NOT NULL DEFAULT 'MOCK', schema_version TEXT NOT NULL DEFAULT '1.0'
);
CREATE INDEX IF NOT EXISTS idx_sensor_pond_time ON sensor_data(pond_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS alarms (
  id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT NOT NULL, pond_id TEXT NOT NULL,
  level TEXT NOT NULL, message TEXT NOT NULL, reason TEXT NOT NULL,
  created_at INTEGER NOT NULL, acknowledged INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_alarm_pond_time ON alarms(pond_id, created_at DESC);

CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, pond_id TEXT NOT NULL, risk_level TEXT NOT NULL,
  probability REAL NOT NULL, horizon_minutes INTEGER NOT NULL, data_source TEXT NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_prediction_pond_time ON predictions(pond_id, created_at DESC);

CREATE TABLE IF NOT EXISTS oxygen_machines (
  machine_id TEXT PRIMARY KEY, pond_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'OFF',
  mode TEXT NOT NULL DEFAULT 'AUTO', last_transition_at INTEGER, last_command_at INTEGER,
  manual_override INTEGER NOT NULL DEFAULT 0, emergency_stop INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS control_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, machine_id TEXT NOT NULL, operator TEXT NOT NULL,
  action TEXT NOT NULL, reason TEXT NOT NULL, result TEXT NOT NULL, created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS simulation_states (
  pond_id TEXT PRIMARY KEY, temperature REAL NOT NULL, ph REAL NOT NULL, do REAL NOT NULL,
  turbidity REAL NOT NULL, tick INTEGER NOT NULL DEFAULT 0, oxygen_on INTEGER NOT NULL DEFAULT 0
);
