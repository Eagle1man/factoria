import { useCallback, useEffect, useState } from 'react'
import { api, type EquipmentResponse } from '../lib/api'
import { Badge, ErrorState, Kpi, Panel, QualityBadge, SkeletonRows, formatNumber } from '../components/ui'

export default function Overview() {
  const [data, setData] = useState<EquipmentResponse | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(() => {
    setLoading(true)
    api
      .equipment()
      .then((value) => {
        setData(value)
        setError(null)
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    load()
    const timer = window.setInterval(load, 5000)
    return () => window.clearInterval(timer)
  }, [load])

  const lines = data?.lines ?? []
  const running = lines.filter((line) => line.running).length
  const loadAvg = lines.length
    ? lines.reduce((sum, line) => sum + (line.load ?? 0), 0) / lines.length
    : 0
  const maxTemp = lines.reduce((max, line) => Math.max(max, line.temp ?? 0), 0)
  const alarms = lines.filter((line) => (line.alarm ?? 0) !== 0).length

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Обзор</h1>
          <div className="page-sub">
            Сводка по трём линиям · данные обновляются каждые 5 секунд
          </div>
        </div>
        {data && (
          <div className="mono faint">
            снимок {new Date(data.snapshot_ts).toLocaleTimeString('ru-RU')} · seq {data.seq}
          </div>
        )}
      </div>

      {error != null ? (
        <Panel>
          <ErrorState
            message={error instanceof Error ? error.message : 'ошибка запроса'}
            onRetry={load}
          />
        </Panel>
      ) : (
        <>
          <div className="grid grid-kpi">
            <Kpi label="Линии в работе" value={`${running} / ${lines.length || 3}`} />
            <Kpi label="Средняя загрузка" value={formatNumber(loadAvg, 0)} unit="%" />
            <Kpi
              label="Максимальная температура"
              value={formatNumber(maxTemp, 1)}
              unit="°C"
              tone={maxTemp > 80 ? 'bad' : maxTemp > 70 ? 'warn' : undefined}
            />
            <Kpi label="Аварии" value={alarms} tone={alarms > 0 ? 'bad' : undefined} />
          </div>

          <Panel title="Состояние линий" hint="значения — последний успешный опрос OPC UA">
            {loading && !data ? (
              <SkeletonRows rows={3} />
            ) : (
              <div className="table-wrap">
                <table className="data">
                  <thead>
                    <tr>
                      <th>Линия</th>
                      <th>Режим</th>
                      <th className="num">Уставка, rpm</th>
                      <th className="num">Обороты, rpm</th>
                      <th className="num">Температура, °C</th>
                      <th className="num">Загрузка, %</th>
                      <th>Рецепт</th>
                      <th>Авария</th>
                      <th>Качество</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lines.map((line) => (
                      <tr key={line.line_id}>
                        <td className="mono">{line.line_id}</td>
                        <td>
                          {line.running ? <Badge tone="good">работа</Badge> : <Badge>стоп</Badge>}
                        </td>
                        <td className="num">{formatNumber(line.speed_sp)}</td>
                        <td className="num">{formatNumber(line.speed_pv)}</td>
                        <td className="num">{formatNumber(line.temp, 1)}</td>
                        <td className="num">{formatNumber(line.load, 0)}</td>
                        <td className="mono">{line.recipe ?? '—'}</td>
                        <td>
                          {(line.alarm ?? 0) !== 0 ? (
                            <Badge tone="bad">код {line.alarm}</Badge>
                          ) : (
                            <span className="faint">—</span>
                          )}
                        </td>
                        <td>
                          <QualityBadge quality={line.quality} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>

          <Panel title="Что дальше" hint="этап 3 продолжается">
            <div className="muted" style={{ fontSize: 12 }}>
              Экран согласований и документы 1С появятся после этапа 4a: сейчас backend
              не принимает команды, поэтому кнопки записи здесь не показываются.
            </div>
          </Panel>
        </>
      )}
    </>
  )
}
