import { useCallback, useEffect, useState } from 'react'
import { ApiError, api, type AuditEvent } from '../lib/api'
import { ErrorState, Panel, SkeletonRows, formatDateTime } from '../components/ui'
import { useAuth } from '../lib/auth'

const KIND_LABEL: Record<string, string> = {
  auth: 'вход',
  command: 'команда',
  validation: 'валидация',
  approval: 'подтверждение',
  execution: 'исполнение',
  agent: 'агент',
  system: 'система',
}

export default function Audit() {
  const { role } = useAuth()
  const [events, setEvents] = useState<AuditEvent[] | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(() => {
    setLoading(true)
    api
      .audit(50)
      .then((value) => {
        setEvents(value.events)
        setError(null)
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  useEffect(load, [load])

  const forbidden = error instanceof ApiError && error.status === 403

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Журнал</h1>
          <div className="page-sub">Только добавление записей · последние 50 событий</div>
        </div>
        <div className="mono faint">роль: {role}</div>
      </div>

      <Panel>
        {loading && !events ? (
          <SkeletonRows rows={6} />
        ) : forbidden ? (
          <ErrorState
            message={`роль «${role}» не имеет доступа к журналу. Войдите как auditor или lead.`}
            code={403}
          />
        ) : error ? (
          <ErrorState
            message={error instanceof Error ? error.message : 'ошибка запроса'}
            onRetry={load}
          />
        ) : events && events.length === 0 ? (
          <div className="empty">
            <div style={{ color: 'var(--ink)', fontSize: 14 }}>Событий пока нет</div>
            <div style={{ fontSize: 12 }}>Журнал заполняется при входе и при работе с командами.</div>
          </div>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Время</th>
                  <th>Тип</th>
                  <th>Кто</th>
                  <th>Действие</th>
                  <th>Объект</th>
                  <th>Корреляция</th>
                </tr>
              </thead>
              <tbody>
                {events?.map((event) => (
                  <tr key={event.id}>
                    <td className="mono">{formatDateTime(event.ts)}</td>
                    <td className="muted">{KIND_LABEL[event.kind] ?? event.kind}</td>
                    <td className="mono">{event.actor}</td>
                    <td>{event.action}</td>
                    <td className="mono faint">{event.subject ?? '—'}</td>
                    <td className="mono faint">{event.correlation_id ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </>
  )
}
