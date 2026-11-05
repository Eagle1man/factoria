import { useEffect, useState } from 'react'
import { api, type Health } from '../lib/api'
import { ErrorState, Panel, SkeletonRows, formatTime } from '../components/ui'

export default function Settings() {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState<unknown>(null)

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch(setError)
  }, [])

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Настройки</h1>
          <div className="page-sub">Подключения и текущее состояние контура · только чтение</div>
        </div>
      </div>

      <Panel title="Подключения" hint="источник — GET /api/v1/health">
        {error ? (
          <ErrorState message={error instanceof Error ? error.message : 'ошибка запроса'} />
        ) : !health ? (
          <SkeletonRows rows={4} />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Параметр</th>
                  <th>Значение</th>
                  <th>Примечание</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="muted">Среда</td>
                  <td className="mono">{health.env}</td>
                  <td className="faint">dev / pilot / production</td>
                </tr>
                <tr>
                  <td className="muted">OPC UA</td>
                  <td className="mono">{health.sources.opcua.endpoint}</td>
                  <td className="faint">
                    {health.sources.opcua.state === 'connected' ? 'связь есть' : 'нет связи'} ·{' '}
                    {formatTime(health.sources.opcua.changed_at)}
                  </td>
                </tr>
                <tr>
                  <td className="muted">База данных</td>
                  <td className="mono">{health.sources.database}</td>
                  <td className="faint">SQLite, миграции Alembic</td>
                </tr>
                <tr>
                  <td className="muted">Теги</td>
                  <td className="mono">
                    {health.tags.total} · не в норме {health.tags.not_good}
                  </td>
                  <td className="faint">21 тег, 3 линии</td>
                </tr>
                <tr>
                  <td className="muted">Снимок</td>
                  <td className="mono">{formatTime(health.snapshot_ts)}</td>
                  <td className="faint">время последнего опроса</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <Panel title="Политика контура" hint="по документации проекта, не по данным health">
        <div className="muted" style={{ fontSize: 12, display: 'grid', gap: 8 }}>
          <div>Запись в 1С отключена: адаптер не имеет методов записи.</div>
          <div>Автономия по умолчанию A1 — любое действие подтверждает человек.</div>
          <div>Внешние API выключены: ALLOW_EXTERNAL_API=false.</div>
          <div>
            Источник: <span className="mono">docs/decisions.md</span>,{' '}
            <span className="mono">docs/autonomy-matrix.md</span>.
          </div>
        </div>
      </Panel>
    </>
  )
}
