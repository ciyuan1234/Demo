export interface Device { device_id: string; pond_id: string; mode: string; status: string }
export interface WaterQuality { timestamp: number; temperature: number; ph: number; do: number; turbidity: number; data_source: string; mode: string }
export interface Alarm { level: string; message: string; pond_id: string; created_at: string; acknowledged: boolean }
export interface Oxygen { machine_id: string; status: string; mode: string }

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
  return response.json() as Promise<T>
}

export const api = {
  devices: () => request<Device[]>('/api/devices'),
  latest: (pondId: string) => request<WaterQuality>(`/api/water-quality/latest?pond_id=${encodeURIComponent(pondId)}`),
  history: (pondId: string) => request<WaterQuality[]>(`/api/water-quality/history?pond_id=${encodeURIComponent(pondId)}&limit=60`),
  alarms: (pondId: string) => request<Alarm[]>(`/api/alarms?pond_id=${encodeURIComponent(pondId)}`),
  oxygen: () => request<Oxygen>('/api/oxygen/status'),
  oxygenCommand: (action: 'start' | 'stop') => request<Oxygen>(`/api/oxygen/${action}`, { method: 'POST' }),
  oxygenMode: (mode: 'AUTO' | 'MANUAL') => request<Oxygen>(`/api/oxygen/mode?mode=${mode}`, { method: 'POST' }),
}
