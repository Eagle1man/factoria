import { useEffect, useMemo, useState } from 'react'
import { api, type ShopStation, type ShopTemplate } from '../lib/api'
import { getToken } from '../lib/api'
import { Download } from 'lucide-react'
import { useTags, qualityOf } from '../lib/stream'
import { Badge, Panel, QualityBadge } from '../components/ui'
import FlowCanvas from '../components/FlowCanvas'
import CoPilotPanel from '../components/CoPilotPanel'

function statusTone(s: string): 'good' | 'warn' | 'bad' | 'info' {
  if (s === 'RUNNING') return 'good'
  if (s === 'BOTTLENECK') return 'bad'
  if (s === 'WARN_QUEUE') return 'warn'
  return 'info'
}

function statusLabel(s: string): string {
  if (s === 'RUNNING') return 'работает'
  if (s === 'BOTTLENECK') return 'узкое место'
  if (s === 'WARN_QUEUE') return 'очередь'
  if (s === 'STANDBY') return 'ожидание'
  return s
}

function StationCard({
  station,
  liveQuality,
  liveValue,
}: {
  station: ShopStation
  liveQuality?: string
  liveValue?: string
}) {
  return (
    <div
      className="panel"
      style={{
        padding: 12,
        borderColor: station.status === 'BOTTLENECK' ? 'var(--danger)' : undefined,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
        <span className="mono muted">{station.id}</span>
        <Badge tone={statusTone(station.status)}>{statusLabel(station.status)}</Badge>
      </div>
      <div style={{ fontWeight: 600, marginTop: 4 }}>{station.name}</div>
      <div className="faint" style={{ marginTop: 4, fontSize: 12 }}>
        {station.type}
        {station.takt_s != null ? ` · такт ${station.takt_s} с` : ''}
        {station.line_id ? ` · ${station.line_id}` : ''}
      </div>
      {station.metric_label && (
        <div className="muted" style={{ marginTop: 6, fontSize: 12 }}>
          {station.metric_label}: <span className="mono">{liveValue ?? station.metric_value ?? '—'}</span>
          {liveQuality && liveQuality !== 'GOOD' && (
            <span style={{ marginLeft: 6 }}>
              <QualityBadge quality={liveQuality as 'GOOD' | 'STALE' | 'BAD'} />
            </span>
          )}
        </div>
      )}
      {station.note && (
        <div className="faint" style={{ marginTop: 4, fontSize: 11 }}>
          {station.note}
        </div>
      )}
    </div>
  )
}

export default function Flow() {
  const [templates, setTemplates] = useState<ShopTemplate[]>([])
  const [selected, setSelected] = useState<string>('cnc_metal')
  const [error, setError] = useState<string | null>(null)
  const { values } = useTags(getToken())

  useEffect(() => {
    let alive = true
    api
      .templates()
      .then((body) => {
        if (!alive) return
        setTemplates(body.templates)
        if (body.templates.length && !body.templates.find((t) => t.id === selected)) {
          setSelected(body.templates[0].id)
        }
      })
      .catch((e) => alive && setError(e instanceof Error ? e.message : 'ошибка'))
    return () => {
      alive = false
    }
  }, [])

  const current = useMemo(
    () => templates.find((t) => t.id === selected) ?? templates[0] ?? null,
    [templates, selected],
  )

  const lineLive = useMemo(() => {
    const out: Record<string, { running?: boolean | null; load?: number | null; alarm?: number | null; temp?: number | null; speedSp?: number | null; quality?: string }> = {}
    for (const line of ['L1', 'L2', 'L3']) {
      const load = values[`${line}.Load.Pct`]
      const alarm = values[`${line}.Alarm.Code`]
      const running = values[`${line}.Running`]
      const temp = values[`${line}.Temp.PV`]
      const sp = values[`${line}.Speed.SP`]
      out[line] = {
        running: typeof running?.v === 'boolean' ? running.v : null,
        load: typeof load?.v === 'number' ? load.v : null,
        alarm: typeof alarm?.v === 'number' ? alarm.v : null,
        temp: typeof temp?.v === 'number' ? temp.v : null,
        speedSp: typeof sp?.v === 'number' ? sp.v : null,
        quality: load ? qualityOf(load) : undefined,
      }
    }
    return out
  }, [values])

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Поток цеха</h1>
          <div className="page-sub">
            Шаблоны витрины (спека Stitch) · живые сигналы берутся из L1-L3 по OPC UA · управление — только через
            согласование
          </div>
        </div>
      </div>

      {error && (
        <div className="panel" style={{ borderColor: 'var(--danger)', marginBottom: 16 }}>
          <span className="muted">Не удалось загрузить шаблоны: {error}</span>
        </div>
      )}

      <Panel title="Шаблон производства" hint="выбор меняет представление; контур 1C/PLC не управляется отсюда">
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {templates.map((t) => (
            <button
              key={t.id}
              className={t.id === selected ? 'btn btn-primary' : 'btn btn-secondary'}
              onClick={() => setSelected(t.id)}
              title={t.description}
            >
              {t.name}
            </button>
          ))}
          {!templates.length && <span className="muted">загрузка…</span>}
        </div>
      </Panel>

      {current && (
        <>
          <Panel
            title="Экспорт (read-only)"
            hint="формируется из реестра/шаблона; отправка в 1C (PUSH/OData) отключена"
            actions={
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  className="btn btn-secondary"
                  onClick={async () => {
                    const t = getToken()
                    const res = await fetch(`/api/v1/exports/1c-enterprise.xml?template_id=${encodeURIComponent(current.id)}`, {
                      headers: t ? { Authorization: `Bearer ${t}` } : {},
                    })
                    const blob = await res.blob()
                    const a = document.createElement('a')
                    a.href = URL.createObjectURL(blob)
                    a.download = `factoria-enterprise-${current.id}.xml`
                    a.click()
                    URL.revokeObjectURL(a.href)
                  }}
                >
                  <Download size={14} style={{ marginRight: 6, verticalAlign: 'text-bottom' }} />
                  1C EnterpriseData
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={async () => {
                    const t = getToken()
                    const res = await fetch('/api/v1/exports/opcua-nodeset2.xml', {
                      headers: t ? { Authorization: `Bearer ${t}` } : {},
                    })
                    const blob = await res.blob()
                    const a = document.createElement('a')
                    a.href = URL.createObjectURL(blob)
                    a.download = 'factoria-opcua-nodeset2.xml'
                    a.click()
                    URL.revokeObjectURL(a.href)
                  }}
                >
                  <Download size={14} style={{ marginRight: 6, verticalAlign: 'text-bottom' }} />
                  OPC UA NodeSet2
                </button>
              </div>
            }
          >
            <div className="muted" style={{ fontSize: 12 }}>
              XML генерируется из реального реестра тегов (<span className="mono">urn:mfg:emulator</span>, 21 тег, 15
              методов по линиям) и выбранного шаблона. Контур 1C остаётся read-only.
            </div>
          </Panel>

          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, marginTop: 16 }}>
            <Panel title="Заказ / план" hint="демонстрационные значения шаблона">
              <div className="muted">
                <div><span className="faint">Заказ</span> <span className="mono">{current.order_number}</span></div>
                <div><span className="faint">Изделие</span> {current.part_name}</div>
                <div><span className="faint">План / факт</span> <span className="mono">{current.fact_quantity} / {current.plan_quantity}</span></div>
                <div><span className="faint">Брак</span> <span className="mono">{current.defects}</span></div>
              </div>
            </Panel>
            <Panel title="Узел ограничения" hint="bottleneck витрины">
              <div>
                <Badge tone="bad">{current.bottleneck_node_id}</Badge>{' '}
                <span className="muted">{current.bottleneck_reason}</span>
              </div>
              <div className="faint" style={{ marginTop: 6, fontSize: 12 }}>
                Целевой выпуск: {current.target_output} · такт {current.takt_time_s} с
                {current.sim_scenario ? ` · сценарий симулятора: ${current.sim_scenario}` : ''}
              </div>
                        {current.sim_scenario && (
              <div style={{ marginTop: 10 }}>
                <button
                  className="btn btn-secondary"
                  onClick={async () => {
                    try {
                      const run = await api.createSimRun(current.sim_scenario!, 42, 180)
                      window.alert(`Прогон: #${run.id} · ${run.scenario} · hash ${run.repro_hash.slice(0, 12)}…`)
                    } catch (e) {
                      window.alert(e instanceof Error ? e.message : 'Ошибка симуляции')
                    }
                  }}
                >
                  Запустить сценарий симулятора (seed 42)
                </button>
              </div>
            )}
          </Panel>
          </div>

          <Panel title="2.5D-схема потока" hint="анимация витрины; подсветка узкого места и аварии по mapped line (L1-L3)">
            <FlowCanvas template={current} lineLive={lineLive} />
          </Panel>

          <CoPilotPanel template={current} lineLive={lineLive} />

          <Panel title="Участки линии" hint="карточки узлов шаблона; живые обороты — из OPC UA там, где есть привязка">
            <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
              {current.stations.map((station: ShopStation) => {
                const line = station.line_id
                const speed = line ? values[`${line}.Speed.PV`] : undefined
                const liveValue =
                  line && station.metric_label?.includes('Обороты') && speed
                    ? `${typeof speed.v === 'number' ? Math.round(speed.v) : speed.v} rpm`
                    : undefined
                return (
                  <StationCard
                    key={station.id}
                    station={station}
                    liveQuality={speed ? qualityOf(speed) : undefined}
                    liveValue={liveValue}
                  />
                )
              })}
            </div>
          </Panel>
        </>
      )}
    </>
  )
}