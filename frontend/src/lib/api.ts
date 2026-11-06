export type Quality = 'GOOD' | 'STALE' | 'BAD'

export interface TagValue {
  v: number | string | boolean | null
  q: Quality
  ts: string | null
}

export interface Snapshot {
  seq: number
  snapshot_ts: string
  values: Record<string, TagValue>
}

export interface LineSummary {
  line_id: string
  running: boolean | null
  speed_sp: number | null
  speed_pv: number | null
  temp: number | null
  load: number | null
  alarm: number | null
  recipe: string | null
  quality: Quality
}

export interface EquipmentResponse {
  lines: LineSummary[]
  snapshot_ts: string
  seq: number
}

export interface Health {
  status: string
  env: string
  sources: {
    opcua: { state: string; changed_at: string | null; endpoint: string }
    database: string
  }
  tags: { total: number; not_good: number }
  snapshot_ts: string
}

export interface AuditEvent {
  id: number
  ts: string
  kind: string
  actor: string
  action: string
  subject: string | null
  payload: Record<string, unknown>
  correlation_id: string | null
}

export interface ValidationStage {
  stage: string
  ok: boolean
  code?: string | null
  detail?: string | null
}

export interface CommandSummary {
  command_id: string
  type: string
  line_id: string
  status: string
  autonomy_level: string
  version: number
  params: Record<string, unknown>
  validation_trace: ValidationStage[]
  expires_at: string | null
  created_at: string | null
}

export interface Order {
  order_id: string
  product: string
  qty: number
  priority: 'low' | 'normal' | 'high'
  due_date: string
  spec_id: string
}

export interface TwinEntity {
  id: string
  kind: string
  name: string
  attributes: Record<string, unknown>
}

export interface TwinRelation {
  from: string
  to: string
  type: string
}

export interface Twin {
  version: string
  status: string
  built_at: string
  basis: {
    registry_version: number
    tags: number
    lines: number
    orders: number
    snapshot_seq: number
  }
  metrics: {
    coverage_pct: number
    tags_good: number
    tags_total: number
    freshness_sec: number | null
    accuracy: number | null
  }
  entities: TwinEntity[]
  relations: TwinRelation[]
  warnings: string[]
}

export interface TwinVersion {
  id: number
  version: string
  built_at: string | null
  status: string
  coverage_pct: number
  tags_good: number
  tags_total: number
  freshness_sec: number | null
  snapshot_seq: number
  warnings: string[]
  delta: { coverage_pct: number | null; tags_good: number | null }
}

const TOKEN_KEY = 'factoria.token'
let token: string | null = sessionStorage.getItem(TOKEN_KEY)

export function setToken(value: string | null): void {
  token = value
  if (value) sessionStorage.setItem(TOKEN_KEY, value)
  else sessionStorage.removeItem(TOKEN_KEY)
}

export function getToken(): string | null {
  return token
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body) headers.set('Content-Type', 'application/json')

  const response = await fetch(path, { ...init, headers })
  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const body = await response.json()
      detail = typeof body.detail === 'string' ? body.detail : detail
    } catch {
      /* тело не JSON — оставляем код */
    }
    throw new ApiError(response.status, detail)
  }
  return (await response.json()) as T
}

export interface LoginResponse {
  access_token: string
  role: string
  expires_in: number
}

export const api = {
  login: (username: string, password: string) =>
    request<LoginResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  me: () => request<{ user_id: string; role: string }>('/api/v1/auth/me'),
  health: () => request<Health>('/api/v1/health'),
  equipment: () => request<EquipmentResponse>('/api/v1/equipment'),
  lineState: (line: string) =>
    request<{ line_id: string } & Snapshot>(`/api/v1/equipment/${line}/state`),
  audit: (limit = 50) => request<{ events: AuditEvent[]; count: number }>(`/api/v1/audit?limit=${limit}`),
  commands: (status?: string) =>
    request<{ commands: CommandSummary[]; count: number }>(
      `/api/v1/commands${status ? `?status=${encodeURIComponent(status)}` : ''}`,
    ),
  command: (id: string) => request<CommandSummary>(`/api/v1/commands/${id}`),
  approve: (id: string, version: number, comment: string) =>
    request<{ command_id: string; status: string; detail: string }>(
      `/api/v1/commands/${id}/approve`,
      { method: 'POST', body: JSON.stringify({ version, comment }) },
    ),
  reject: (id: string, version: number, reason: string) =>
    request<{ command_id: string; status: string }>(`/api/v1/commands/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ version, reason }),
    }),
  orders: () => request<{ source: string; orders: Order[] }>('/api/v1/orders'),
  order: (id: string) => request<Order>(`/api/v1/orders/${id}`),
  twin: () => request<Twin>('/api/v1/twin'),
  twinHistory: (limit = 20) =>
    request<{ versions: TwinVersion[]; count: number }>(`/api/v1/twin/history?limit=${limit}`),
  twinSnapshot: () => request<TwinVersion>('/api/v1/twin/snapshot', { method: 'POST' }),
}
