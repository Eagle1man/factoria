/**
 * Демо-режим для GitHub Pages: тот же React-интерфейс, но backend заменён
 * браузерной реализацией API и WebSocket. Данные имитированы; запись в 1C/PLC
 * отсутствует. Живой контур — локально (FastAPI + OPC UA).
 */
import data from './data.json'

type Quality = 'GOOD' | 'STALE' | 'BAD'
interface TagValue {
  v: number | string | boolean | null
  q: Quality
  ts: string | null
}

const LINES = data.registry.lines as string[]
const BASE: Record<string, number> = { L1: 760, L2: 690, L3: 720 }
const T0 = Date.now()

let seq = 0
let tick = 0
const tags: Record<string, TagValue> = {}

const nowIso = () => new Date().toISOString()

function initTags(): void {
  for (const line of LINES) {
    const base = BASE[line] ?? 700
    tags[`${line}.Running`] = { v: true, q: 'GOOD', ts: nowIso() }
    tags[`${line}.Speed.SP`] = { v: base, q: 'GOOD', ts: nowIso() }
    tags[`${line}.Speed.PV`] = { v: base, q: 'GOOD', ts: nowIso() }
    tags[`${line}.Temp.PV`] = { v: 58, q: 'GOOD', ts: nowIso() }
    tags[`${line}.Load.Pct`] = { v: 78, q: 'GOOD', ts: nowIso() }
    tags[`${line}.Alarm.Code`] = { v: 0, q: 'GOOD', ts: nowIso() }
    tags[`${line}.Recipe.ID`] = { v: 'R1', q: 'GOOD', ts: nowIso() }
  }
}

function setTag(id: string, v: TagValue['v'], changed: Record<string, TagValue>): void {
  const ts = nowIso()
  tags[id] = { v, q: 'GOOD', ts }
  changed[id] = tags[id]
}

function updateTags(): Record<string, TagValue> {
  seq += 1
  tick += 1
  const changed: Record<string, TagValue> = {}
  for (const line of LINES) {
    const base = BASE[line] ?? 700
    const phase = base / 100
    const speed = Math.max(0, Math.round(base + Math.sin(tick / 7 + phase) * 45 + (Math.random() * 10 - 5)))
    const temp = 56 + Math.sin(tick / 11 + phase) * 6 + Math.random() * 1.5
    const load = 74 + Math.sin(tick / 9 + phase) * 9 + Math.random() * 2
    setTag(`${line}.Speed.PV`, speed, changed)
    setTag(`${line}.Temp.PV`, Number(temp.toFixed(1)), changed)
    setTag(`${line}.Load.Pct`, Number(load.toFixed(1)), changed)
  }
  return changed
}

initTags()

// ---------------- WebSocket ----------------

const sockets = new Set<DemoWebSocket>()

class DemoWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  url: string
  readyState = 0
  onopen: ((ev: Event) => void) | null = null
  onmessage: ((ev: MessageEvent) => void) | null = null
  onclose: ((ev: CloseEvent) => void) | null = null
  onerror: ((ev: Event) => void) | null = null

  constructor(url: string | URL) {
    this.url = String(url)
    window.setTimeout(() => {
      this.readyState = DemoWebSocket.OPEN
      sockets.add(this)
      this.onopen?.(new Event('open'))
    }, 30)
  }

  send(raw: string): void {
    try {
      const message = JSON.parse(raw) as { type?: string }
      if (message.type === 'subscribe' || message.type === 'resume') {
        this.emit({ type: 'snapshot', seq, values: { ...tags } })
      }
    } catch {
      /* ignore malformed frames */
    }
  }

  emit(payload: unknown): void {
    this.onmessage?.({ data: JSON.stringify(payload) } as MessageEvent)
  }

  close(): void {
    this.readyState = DemoWebSocket.CLOSED
    sockets.delete(this)
    this.onclose?.(new CloseEvent('close'))
  }

  addEventListener(): void {
    /* not used by the app */
  }
  removeEventListener(): void {
    /* not used by the app */
  }
  dispatchEvent(): boolean {
    return true
  }
}

function broadcast(payload: unknown): void {
  for (const socket of sockets) socket.emit(payload)
}

// ---------------- commands / sim / twin ----------------

interface DemoCommand {
  command_id: string
  type: string
  line_id: string
  status: string
  autonomy_level: string
  version: number
  params: Record<string, unknown>
  validation_trace: Array<{ stage: string; ok: boolean; code?: string | null; detail?: string | null }>
  expires_at: string | null
  created_at: string | null
}

const commands: DemoCommand[] = []
const simRuns: Array<Record<string, unknown>> = []
let simId = 0

function submitCommand(body: Record<string, unknown>): DemoCommand {
  const target = (body.target as { line_id?: string } | undefined)?.line_id ?? 'L1'
  const command: DemoCommand = {
    command_id: String(body.command_id ?? `cmd-demo-${Date.now()}`),
    type: String(body.type ?? 'set_setpoint'),
    line_id: target,
    status: 'AWAITING_APPROVAL',
    autonomy_level: 'A1',
    version: 1,
    params: (body.params as Record<string, unknown>) ?? {},
    validation_trace: [{ stage: 'demo', ok: true, code: null, detail: 'статическое демо' }],
    expires_at: new Date(Date.now() + 5 * 60_000).toISOString(),
    created_at: nowIso(),
  }
  commands.unshift(command)
  broadcast({
    type: 'command_status',
    command_id: command.command_id,
    status: command.status,
    autonomy_level: command.autonomy_level,
    line_id: command.line_id,
  })
  return command
}

function twin() {
  const entities = LINES.map((line) => ({
    id: line,
    kind: 'line',
    name: `Линия ${line}`,
    attributes: {
      running: tags[`${line}.Running`]?.v ?? null,
      speed_pv: tags[`${line}.Speed.PV`]?.v ?? null,
      temp: tags[`${line}.Temp.PV`]?.v ?? null,
      load: tags[`${line}.Load.Pct`]?.v ?? null,
      recipe: tags[`${line}.Recipe.ID`]?.v ?? null,
    },
  }))
  return {
    version: `demo-${seq}`,
    status: 'ok',
    built_at: nowIso(),
    basis: { registry_version: 1, tags: 21, lines: LINES.length, orders: 0, snapshot_seq: seq },
    metrics: { coverage_pct: 100, tags_good: 21, tags_total: 21, freshness_sec: 0, accuracy: null },
    entities,
    relations: [],
    warnings: ['статическое демо: данные имитированы'],
  }
}

// ---------------- XML ----------------

function xmlEscape(value: unknown): string {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function enterpriseXml(templateId: string | null): string {
  const tpl =
    data.templates.find((t) => t.id === templateId) ?? data.templates[0]
  const now = new Date().toISOString().slice(0, 19)
  return `<?xml version="1.0" encoding="UTF-8"?>
<EnterpriseData xmlns="http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.14" formatVersion="1.14">
  <Header>
    <FormatVersion>1.14</FormatVersion>
    <CreationDateTime>${now}</CreationDateTime>
    <SourceApplication>FACTORIA &amp; AI (read-only export, demo)</SourceApplication>
  </Header>
  <Body>
    <Document.СменноСуточноеЗадание>
      <Номер>${xmlEscape(tpl.order_number)}</Номер>
      <Дата>${now.slice(0, 10)}</Дата>
      <Подразделение>Линии ${LINES.join(', ')} (${xmlEscape(tpl.name)})</Подразделение>
      <Номенклатура>${xmlEscape(tpl.part_name)}</Номенклатура>
      <План>${tpl.plan_quantity}</План>
      <Факт>${tpl.fact_quantity}</Факт>
      <Брак>${tpl.defects}</Брак>
      <Статус>Выгружено_ТолькоЧтение</Статус>
      <Примечание>Экспорт сформирован в демо-режиме. Отправка в 1C (PUSH/OData) отключена: контур 1C — read-only.</Примечание>
    </Document.СменноСуточноеЗадание>
  </Body>
</EnterpriseData>`
}

const DT: Record<string, string> = { bool: 'i=1', float: 'i=11', uint16: 'i=5', string: 'i=12' }

function nodesetXml(): string {
  const reg = data.registry
  let variables = ''
  for (const tag of reg.tags) {
    variables += `  <UAVariable NodeId="ns=1;s=${xmlEscape(tag.id)}" BrowseName="1:${xmlEscape(tag.name)}" DataType="${DT[tag.type] ?? 'i=24'}" AccessLevel="1">
    <DisplayName>${xmlEscape(tag.id)}</DisplayName>
    <Description>line=${xmlEscape(tag.id.split('.')[0])}, type=${tag.type}, unit=${tag.unit ?? '-'}, max_age=${tag.max_age}s, writable=${tag.writable}</Description>
  </UAVariable>\n`
  }
  let methods = ''
  for (const method of reg.methods) {
    for (const line of LINES) {
      methods += `  <UAMethod NodeId="ns=1;s=${line}.${xmlEscape(method.name)}" BrowseName="1:${xmlEscape(method.name)}" Executable="true" UserExecutable="false"/>\n`
    }
  }
  return `<?xml version="1.0" encoding="utf-8"?>
<UANodeSet xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://opcfoundation.org/UA/2011/03/UANodeSet.xsd">
  <NamespaceUris>
    <Uri>${xmlEscape(reg.namespace)}</Uri>
  </NamespaceUris>
${variables}${methods}</UANodeSet>`
}

// ---------------- fetch ----------------

const realFetch = window.fetch.bind(window)

const json = (body: unknown, status = 200): Response =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })

function requestBody<T>(init?: RequestInit): T | null {
  try {
    return typeof init?.body === 'string' ? (JSON.parse(init.body) as T) : null
  } catch {
    return null
  }
}

function lineSummary(line: string) {
  return {
    line_id: line,
    running: tags[`${line}.Running`]?.v ?? null,
    speed_sp: tags[`${line}.Speed.SP`]?.v ?? null,
    speed_pv: tags[`${line}.Speed.PV`]?.v ?? null,
    temp: tags[`${line}.Temp.PV`]?.v ?? null,
    load: tags[`${line}.Load.Pct`]?.v ?? null,
    alarm: tags[`${line}.Alarm.Code`]?.v ?? null,
    recipe: tags[`${line}.Recipe.ID`]?.v ?? null,
    quality: 'GOOD' as Quality,
  }
}

async function handleApi(fullPath: string, method: string, init?: RequestInit): Promise<Response> {
  const [path, query = ''] = fullPath.split('?')
  const params = new URLSearchParams(query)

  if (path === '/api/v1/health') {
    return json({
      status: 'ok',
      env: 'demo',
      sources: {
        opcua: { state: 'connected', changed_at: nowIso(), endpoint: 'demo://opcua' },
        database: 'ok',
      },
      llm: { provider: 'none', configured: false, reachable: false, model: null, detail: 'disabled' },
      tags: { total: 21, not_good: 0 },
      snapshot_ts: nowIso(),
    })
  }

  if (path === '/api/v1/auth/me') return json({ user_id: 'demo-operator', role: 'production_specialist' })
  if (path === '/api/v1/auth/ws-ticket') return json({ ticket: 'demo-ticket', expires_in: 30 })
  if (path === '/api/v1/auth/login') {
    return json({ access_token: 'demo', refresh_token: 'demo-refresh', role: 'production_specialist', expires_in: 900 })
  }
  if (path === '/api/v1/auth/refresh') {
    return json({ access_token: 'demo', refresh_token: 'demo-refresh', role: 'production_specialist', expires_in: 900 })
  }
  if (path === '/api/v1/auth/logout') return json({})

  if (path === '/api/v1/templates') {
    return json({ templates: data.templates, count: data.templates.length })
  }
  if (path.startsWith('/api/v1/templates/')) {
    const id = path.split('/').pop()
    const found = data.templates.find((t) => t.id === id)
    return found ? json(found) : json({ detail: 'шаблон не найден' }, 404)
  }

  if (path === '/api/v1/equipment') {
    return json({ lines: LINES.map(lineSummary), snapshot_ts: nowIso(), seq })
  }
  const lineState = path.match(/^\/api\/v1\/equipment\/([^/]+)\/state$/)
  if (lineState) {
    const line = decodeURIComponent(lineState[1])
    if (!LINES.includes(line)) return json({ detail: 'линия не найдена' }, 404)
    const values = Object.fromEntries(
      Object.entries(tags).filter(([key]) => key.startsWith(`${line}.`)),
    )
    return json({ line_id: line, seq, snapshot_ts: nowIso(), values })
  }

  if (path === '/api/v1/commands' && method === 'GET') {
    return json({ commands, count: commands.length })
  }
  if (path === '/api/v1/commands' && method === 'POST') {
    const body = requestBody<Record<string, unknown>>(init) ?? {}
    return json(submitCommand(body), 202)
  }
  const commandAction = path.match(/^\/api\/v1\/commands\/([^/]+)\/(approve|reject)$/)
  if (commandAction) {
    const command = commands.find((item) => item.command_id === commandAction[1])
    if (!command) return json({ detail: 'команда не найдена' }, 404)
    command.status = commandAction[2] === 'approve' ? 'EXECUTED' : 'REJECTED'
    command.version += 1
    broadcast({
      type: 'command_status',
      command_id: command.command_id,
      status: command.status,
      autonomy_level: command.autonomy_level,
      line_id: command.line_id,
    })
    return json({ command_id: command.command_id, status: command.status, detail: 'demo' })
  }
  if (path.startsWith('/api/v1/commands/')) {
    const id = path.split('/').pop()
    const command = commands.find((item) => item.command_id === id)
    return command ? json(command) : json({ detail: 'команда не найдена' }, 404)
  }

  if (path === '/api/v1/exports/1c-enterprise.xml') {
    return new Response(enterpriseXml(params.get('template_id')), {
      headers: { 'Content-Type': 'application/xml; charset=utf-8' },
    })
  }
  if (path === '/api/v1/exports/opcua-nodeset2.xml') {
    return new Response(nodesetXml(), {
      headers: { 'Content-Type': 'application/xml; charset=utf-8' },
    })
  }

  if (path === '/api/v1/sim/scenarios') {
    return json({
      scenarios: [
        { name: 'nominal', title: 'Номинальный режим', description: 'демо' },
        { name: 'overload', title: 'Перегруз линии', description: 'демо' },
        { name: 'recipe_change', title: 'Смена рецепта', description: 'демо' },
        { name: 'hot_start', title: 'Горячий старт', description: 'демо' },
        { name: 'noisy', title: 'Номинал с возмущениями', description: 'демо' },
      ],
    })
  }
  if (path === '/api/v1/sim/runs' && method === 'POST') {
    const body = requestBody<{ scenario?: string; seed?: number; horizon_s?: number }>(init) ?? {}
    simId += 1
    const run = {
      id: simId,
      scenario: body.scenario ?? 'nominal',
      seed: body.seed ?? 1,
      horizon_s: body.horizon_s ?? 180,
      status: 'done',
      metrics: {
        output_index: 42 + simId,
        max_temp: 78.4,
        avg_load: 81.2,
        uptime_pct: 97.5,
        alarms: 0,
        first_alarm_s: null,
        final_recipe: 'R1',
      },
      events: [],
      repro_hash: `demo-${simId}-${body.seed ?? 1}`,
      created_at: nowIso(),
      created_by: 'demo-operator',
    }
    simRuns.unshift(run)
    return json(run, 201)
  }
  if (path === '/api/v1/sim/runs') {
    return json({ runs: simRuns, count: simRuns.length })
  }
  if (path.startsWith('/api/v1/sim/runs/compare')) {
    return json({
      from: { id: 1, scenario: 'nominal', seed: 42 },
      to: { id: 2, scenario: 'overload', seed: 42 },
      metrics: { from: {}, to: {} },
      delta: { output_index: 0, max_temp: 0, avg_load: 0, uptime_pct: 0, alarms: 0 },
      same_repro: false,
    })
  }
  if (path.startsWith('/api/v1/sim/runs/')) {
    const id = Number(path.split('/').pop())
    const run = simRuns.find((item) => Number(item.id) === id)
    return run ? json(run) : json({ detail: 'прогон не найден' }, 404)
  }

  if (path === '/api/v1/twin') return json(twin())
  if (path === '/api/v1/twin/history') return json({ versions: [], count: 0 })
  if (path === '/api/v1/twin/snapshot' && method === 'POST') {
    return json({
      id: 1,
      version: `demo-${seq}`,
      built_at: nowIso(),
      status: 'ok',
      coverage_pct: 100,
      tags_good: 21,
      tags_total: 21,
      freshness_sec: 0,
      snapshot_seq: seq,
      warnings: [],
      delta: { coverage_pct: null, tags_good: null },
    }, 201)
  }
  if (path.startsWith('/api/v1/twin/compare')) {
    return json({ from: { id: 1, built_at: nowIso() }, to: { id: 1, built_at: nowIso() }, coverage_pct: 0, tags_good: 0, freshness_sec: 0, version_changed: false })
  }

  if (path === '/api/v1/orders') {
    return json({
      source: 'demo',
      orders: [
        { order_id: '#1489-M', product: 'ВТУЛКА-45М', qty: 500, priority: 'normal', due_date: '2026-11-08', spec_id: 'R1' },
      ],
    })
  }
  if (path.startsWith('/api/v1/orders/')) {
    return json({ order_id: '#1489-M', product: 'ВТУЛКА-45М', qty: 500, priority: 'normal', due_date: '2026-11-08', spec_id: 'R1' })
  }

  if (path === '/api/v1/audit') return json({ events: [], count: 0 })

  return json({ detail: `demo: endpoint ${path} не реализован` }, 404)
}

async function patchedFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const raw = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url
  const url = new URL(raw, location.href)
  if (!url.pathname.startsWith('/api/')) return realFetch(input as RequestInfo, init)
  const method = (init?.method ?? 'GET').toUpperCase()
  return handleApi(url.pathname + url.search, method, init)
}

window.fetch = patchedFetch as typeof window.fetch
window.WebSocket = DemoWebSocket as unknown as typeof WebSocket

// телеметрия: обновление и рассылка
window.setInterval(() => {
  const changed = updateTags()
  if (Object.keys(changed).length > 0) {
    broadcast({ type: 'delta', seq, values: changed })
  }
}, 700)

// стартовый сдвиг, чтобы значения не выглядели статичными
for (let i = 0; i < 3; i += 1) updateTags()

export function installMock(): void {
  // патчи уже применены при импорте модуля
  void T0
}
