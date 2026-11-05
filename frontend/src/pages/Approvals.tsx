import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, getToken, type CommandSummary, type TagValue } from '../lib/api'
import { useTags } from '../lib/stream'
import { Badge, ErrorState, Panel, SkeletonRows, formatNumber, formatTime } from '../components/ui'

const TYPE_LABEL: Record<string, string> = {
  set_setpoint: 'Уставка скорости',
  switch_recipe: 'Смена рецепта',
  line_start: 'Пуск линии',
  line_stop: 'Останов линии',
  reallocate_job: 'Перераспределение заказа',
}

function secondsLeft(iso: string | null, tick: number): number | null {
  void tick
  if (!iso) return null
  return Math.max(0, Math.floor((new Date(iso).getTime() - Date.now()) / 1000))
}

function before(command: CommandSummary, values: Record<string, TagValue>): string {
  const line = command.line_id
  switch (command.type) {
    case 'set_setpoint': {
      const sp = values[`${line}.Speed.SP`]?.v
      return typeof sp === 'number' ? `${formatNumber(sp)} rpm` : '—'
    }
    case 'switch_recipe': {
      const recipe = values[`${line}.Recipe.ID`]?.v
      return typeof recipe === 'string' ? recipe : '—'
    }
    case 'line_start':
      return 'линия остановлена'
    case 'line_stop':
      return 'линия работает'
    default:
      return '—'
  }
}

function after(command: CommandSummary): string {
  const params = command.params ?? {}
  switch (command.type) {
    case 'set_setpoint': {
      const value = params.setpoint_value
      return typeof value === 'number' ? `${formatNumber(value)} rpm` : '—'
    }
    case 'switch_recipe':
      return typeof params.recipe_id === 'string' ? params.recipe_id : '—'
    case 'line_start':
      return 'линия работает'
    case 'line_stop':
      return 'линия остановлена'
    case 'reallocate_job':
      return typeof params.job_id === 'string' ? `заказ ${params.job_id}` : '—'
    default:
      return '—'
  }
}

export default function Approvals() {
  const [items, setItems] = useState<CommandSummary[] | null>(null)
  const [a2, setA2] = useState<CommandSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [values, setValues] = useState<Record<string, TagValue>>({})
  const [error, setError] = useState<unknown>(null)
  const [comment, setComment] = useState('')
  const [ack, setAck] = useState(false)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  const load = useCallback(() => {
    api
      .commands()
      .then((result) => {
        setItems(result.commands.filter((command) => command.status === 'AWAITING_APPROVAL'))
        setA2(result.commands.filter((command) => command.autonomy_level === 'A2').slice(0, 5))
        setError(null)
      })
      .catch(setError)
  }, [])

  const { commandEvent } = useTags(getToken())

  useEffect(() => {
    if (commandEvent) load()
  }, [commandEvent, load])

  useEffect(() => {
    load()
    const timer = window.setInterval(load, 5000)
    return () => window.clearInterval(timer)
  }, [load])

  useEffect(() => {
    const timer = window.setInterval(() => setTick((value) => value + 1), 1000)
    return () => window.clearInterval(timer)
  }, [])

  const selected = useMemo(
    () => items?.find((item) => item.command_id === selectedId) ?? null,
    [items, selectedId],
  )

  const selectedKey = selected?.command_id

  useEffect(() => {
    if (!selectedKey) return
    const line = selected?.line_id ?? 'L1'
    api
      .lineState(line)
      .then((state) => setValues(state.values))
      .catch(() => setValues({}))
    setComment('')
    setAck(false)
    setActionError(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedKey])

  const left = selected ? secondsLeft(selected.expires_at, tick) : null
  const expired = left !== null && left <= 0
  const canApprove = comment.trim().length >= 10 && ack && !expired && !busy
  const canReject = comment.trim().length >= 3 && !busy

  async function act(kind: 'approve' | 'reject') {
    if (!selected) return
    setBusy(true)
    setActionError(null)
    try {
      if (kind === 'approve') {
        await api.approve(selected.command_id, selected.version, comment.trim())
      } else {
        await api.reject(selected.command_id, selected.version, comment.trim())
      }
      setSelectedId(null)
      load()
    } catch (problem) {
      setActionError(problem instanceof Error ? problem.message : 'действие не выполнено')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Согласования</h1>
          <div className="page-sub">
            Действия агентов, требующие человека · A1 по умолчанию · решение необратимо
          </div>
        </div>
        <div className="mono faint">{items ? `в очереди: ${items.length}` : '—'}</div>
      </div>

      {error != null ? (
        <Panel>
          <ErrorState
            message={error instanceof Error ? error.message : 'ошибка запроса'}
            onRetry={load}
          />
        </Panel>
      ) : !items ? (
        <Panel>
          <SkeletonRows rows={4} />
        </Panel>
      ) : items.length === 0 ? (
        <Panel>
          <div className="empty">
            <div style={{ color: 'var(--ink)', fontSize: 14 }}>Очередь пуста</div>
            <div style={{ fontSize: 12 }}>
              Ни одно действие не ждёт решения. Когда агент предложит команду, карточка появится
              здесь.
            </div>
          </div>
        </Panel>
      ) : (
        <div className="approvals">
          <div className="queue">
            {items.map((item) => (
              <button
                key={item.command_id}
                className={`queue-item${item.command_id === selectedId ? ' active' : ''}`}
                onClick={() => setSelectedId(item.command_id)}
              >
                <div className="queue-title">{TYPE_LABEL[item.type] ?? item.type}</div>
                <div className="queue-meta mono">
                  {item.line_id} · {item.autonomy_level} · {secondsLeft(item.expires_at, tick)} c
                </div>
              </button>
            ))}
          </div>

          {selected ? (
            <Panel
              title={`${TYPE_LABEL[selected.type] ?? selected.type} · ${selected.line_id}`}
              hint={`команда ${selected.command_id.slice(0, 8)} · создана ${
                selected.created_at ? formatTime(selected.created_at) : '—'
              }`}
              actions={
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <Badge tone={expired ? 'bad' : 'warn'}>{expired ? 'истекло' : `${left} c`}</Badge>
                  <Badge>{selected.autonomy_level}</Badge>
                </div>
              }
            >
              <div className="was-now">
                <div>
                  <div className="kpi-label">Было</div>
                  <div className="mono was-now-value">{before(selected, values)}</div>
                </div>
                <div>
                  <div className="kpi-label">Станет</div>
                  <div className="mono was-now-value accent">{after(selected)}</div>
                </div>
              </div>

              <table className="data" style={{ marginTop: 12 }}>
                <tbody>
                  <tr>
                    <td className="muted">Температура линии</td>
                    <td className="num">
                      {formatNumber(Number(values[`${selected.line_id}.Temp.PV`]?.v ?? 0), 1)} °C
                    </td>
                  </tr>
                  <tr>
                    <td className="muted">Загрузка линии</td>
                    <td className="num">
                      {formatNumber(Number(values[`${selected.line_id}.Load.Pct`]?.v ?? 0), 0)} %
                    </td>
                  </tr>
                  <tr>
                    <td className="muted">Уровень автономии</td>
                    <td className="num">{selected.autonomy_level}</td>
                  </tr>
                </tbody>
              </table>

              <div className="field" style={{ marginTop: 16 }}>
                <label htmlFor="comment">Комментарий (не короче 10 символов)</label>
                <textarea
                  id="comment"
                  className="input"
                  style={{ height: 64, padding: 8, resize: 'vertical' }}
                  value={comment}
                  onChange={(event) => setComment(event.target.value)}
                  placeholder="Что проверили перед решением"
                />
              </div>

              <label className="checkbox-row">
                <input type="checkbox" checked={ack} onChange={(event) => setAck(event.target.checked)} />
                Я проверил состояние линии и понимаю последствия
              </label>

              {actionError && <div className="form-error">{actionError}</div>}

              <div className="approval-actions">
                <button
                  className="btn btn-danger btn-operator"
                  disabled={!canReject || expired}
                  onClick={() => act('reject')}
                >
                  Отклонить
                </button>
                <button
                  className="btn btn-primary btn-operator"
                  disabled={!canApprove || expired}
                  onClick={() => act('approve')}
                >
                  Согласовать
                </button>
              </div>

              <div className="faint" style={{ fontSize: 12, marginTop: 8 }}>
                Подтверждение исполняет команду сразу: backend отправит method-вызов на линию
                и запишет событие в журнал. Отмена после подтверждения невозможна.
              </div>
            </Panel>
          ) : (
            <Panel>
              <div className="empty">
                <div style={{ color: 'var(--ink)', fontSize: 14 }}>Выберите карточку слева</div>
                <div style={{ fontSize: 12 }}>В карточке — что изменится и чем это грозит.</div>
              </div>
            </Panel>
          )}
        </div>
      )}

      <Panel
        title="Автономные действия (A2)"
        hint="исполнены без человека, событие записано в журнал"
      >
        {a2.length === 0 ? (
          <div className="muted" style={{ fontSize: 12 }}>
            Пока нет автоматических действий. Они разрешаются флагом{' '}
            <span className="mono">AUTONOMY_MAX=A2</span> и только для уставки в безопасном
            коридоре.
          </div>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Время</th>
                  <th>Действие</th>
                  <th>Линия</th>
                  <th>Статус</th>
                </tr>
              </thead>
              <tbody>
                {a2.map((command) => (
                  <tr key={command.command_id}>
                    <td className="mono">
                      {command.created_at ? formatTime(command.created_at) : '—'}
                    </td>
                    <td>{TYPE_LABEL[command.type] ?? command.type}</td>
                    <td className="mono">{command.line_id}</td>
                    <td>
                      <Badge tone={command.status === 'EXECUTED' ? 'good' : 'warn'}>
                        {command.status.toLowerCase()}
                      </Badge>
                    </td>
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
