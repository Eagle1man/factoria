import { useCallback, useEffect, useState } from 'react'
import { api, type EquipmentResponse, type Twin, type TwinVersion } from '../lib/api'
import { useAuth } from '../lib/auth'
import {
  Badge,
  ErrorState,
  Kpi,
  Panel,
  QualityBadge,
  SkeletonRows,
  formatNumber,
  formatTime,
} from '../components/ui'

const KIND_LABEL: Record<string, string> = {
  enterprise: 'предприятие',
  line: 'линия',
  tag: 'сигнал',
  order: 'заказ',
  spec: 'спецификация',
}

export default function TwinPage() {
  const { role } = useAuth()
  const [twin, setTwin] = useState<Twin | null>(null)
  const [equipment, setEquipment] = useState<EquipmentResponse | null>(null)
  const [history, setHistory] = useState<TwinVersion[]>([])
  const [error, setError] = useState<unknown>(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    Promise.all([api.twin(), api.equipment(), api.twinHistory(10)])
      .then(([twinData, equipmentData, historyData]) => {
        setTwin(twinData)
        setEquipment(equipmentData)
        setHistory(historyData.versions)
        setError(null)
      })
      .catch(setError)
  }, [])

  async function snapshot() {
    setBusy(true)
    try {
      await api.twinSnapshot()
      load()
    } catch (problem) {
      setError(problem)
    } finally {
      setBusy(false)
    }
  }

  const canSnapshot = role === 'production_specialist' || role === 'technologist'

  useEffect(() => {
    load()
    const timer = window.setInterval(load, 10_000)
    return () => window.clearInterval(timer)
  }, [load])

  if (error) {
    return (
      <Panel>
        <ErrorState
          message={error instanceof Error ? error.message : 'ошибка запроса'}
          onRetry={load}
        />
      </Panel>
    )
  }

  if (!twin) {
    return (
      <Panel>
        <SkeletonRows rows={5} />
      </Panel>
    )
  }

  const counts = twin.entities.reduce<Record<string, number>>((acc, entity) => {
    acc[entity.kind] = (acc[entity.kind] ?? 0) + 1
    return acc
  }, {})

  const lines = twin.entities.filter((entity) => entity.kind === 'line')
  const quality = new Map((equipment?.lines ?? []).map((line) => [line.line_id, line.quality]))

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Цифровой двойник</h1>
          <div className="page-sub">
            Представление структуры и качества данных · версия{' '}
            <span className="mono">{twin.version}</span> · собрано {formatTime(twin.built_at)}
          </div>
        </div>
        <Badge tone="warn">{twin.status}</Badge>
      </div>

      <div className="grid grid-kpi">
        <Kpi
          label="Покрытие данными"
          value={formatNumber(twin.metrics.coverage_pct, 1)}
          unit="%"
          tone={twin.metrics.coverage_pct < 100 ? 'warn' : undefined}
        />
        <Kpi
          label="Сигналов в норме"
          value={`${twin.metrics.tags_good} / ${twin.metrics.tags_total}`}
        />
        <Kpi
          label="Свежесть данных"
          value={twin.metrics.freshness_sec === null ? '—' : formatNumber(twin.metrics.freshness_sec, 1)}
          unit="c"
        />
        <Kpi label="Точность" value="не измерена" />
      </div>

      <Panel title="Предупреждения" hint="что нельзя считать проверенным">
        <ul className="muted" style={{ margin: 0, paddingLeft: 18, fontSize: 12, display: 'grid', gap: 6 }}>
          {twin.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      </Panel>

      <Panel title="Сущности" hint={`всего ${twin.entities.length} · связей ${twin.relations.length}`}>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Тип</th>
                <th className="num">Количество</th>
                <th>Что это</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(counts).map(([kind, count]) => (
                <tr key={kind}>
                  <td className="mono">{kind}</td>
                  <td className="num">{count}</td>
                  <td className="muted">{KIND_LABEL[kind] ?? kind}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Линии" hint="структура из registry.yaml, качество — из кэша">
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Линия</th>
                <th className="num">Сигналов</th>
                <th className="num">Макс. уставка, rpm</th>
                <th>Рецепты</th>
                <th>Качество</th>
              </tr>
            </thead>
            <tbody>
              {lines.map((line) => (
                <tr key={line.id}>
                  <td className="mono">{line.id}</td>
                  <td className="num">{String(line.attributes.tags ?? '—')}</td>
                  <td className="num">{String(line.attributes.speed_max ?? '—')}</td>
                  <td className="mono faint">
                    {Array.isArray(line.attributes.recipes) ? line.attributes.recipes.join(' ') : '—'}
                  </td>
                  <td>
                    <QualityBadge quality={(quality.get(line.id) ?? 'BAD') as 'GOOD' | 'STALE' | 'BAD'} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="faint" style={{ fontSize: 12, marginTop: 12 }}>
          Двойник — детерминированное представление реестра и кэша, а не обученная модель.
          Точность скрыта намеренно: для неё нужен валидированный набор исторических данных.
        </div>
      </Panel>

      <Panel
        title="История срезов"
        hint="каждый срез — факт на момент времени, без ретроспективных правок"
        actions={
          canSnapshot ? (
            <button className="btn btn-secondary" onClick={snapshot} disabled={busy}>
              {busy ? 'Снимаю…' : 'Снять срез'}
            </button>
          ) : null
        }
      >
        {history.length === 0 ? (
          <div className="muted" style={{ fontSize: 12 }}>
            Срезов пока нет. Нажмите «Снять срез», чтобы зафиксировать текущее качество данных.
          </div>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Время</th>
                  <th>Версия</th>
                  <th className="num">Покрытие, %</th>
                  <th className="num">Сигналов</th>
                  <th className="num">Δ покрытия</th>
                  <th className="num">Δ сигналов</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => {
                  const delta = item.delta.coverage_pct
                  const tone =
                    delta === null ? undefined : delta > 0 ? 'var(--success)' : delta < 0 ? 'var(--danger)' : 'var(--ink-muted)'
                  return (
                    <tr key={item.id}>
                      <td className="mono">
                        {item.built_at ? formatTime(item.built_at) : '—'}
                      </td>
                      <td className="mono faint">{item.version}</td>
                      <td className="num">{formatNumber(item.coverage_pct, 1)}</td>
                      <td className="num">
                        {item.tags_good} / {item.tags_total}
                      </td>
                      <td className="num" style={tone ? { color: tone } : undefined}>
                        {delta === null ? '—' : `${delta > 0 ? '+' : ''}${formatNumber(delta, 2)}`}
                      </td>
                      <td className="num muted">
                        {item.delta.tags_good === null
                          ? '—'
                          : `${item.delta.tags_good > 0 ? '+' : ''}${item.delta.tags_good}`}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </>
  )
}
