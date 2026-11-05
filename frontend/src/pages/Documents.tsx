import { useCallback, useEffect, useState } from 'react'
import { api, type Order } from '../lib/api'
import { Badge, EmptyState, ErrorState, Panel, SkeletonRows } from '../components/ui'

const PRIORITY: Record<string, { label: string; tone: 'bad' | 'warn' | 'info' }> = {
  high: { label: 'высокий', tone: 'bad' },
  normal: { label: 'обычный', tone: 'warn' },
  low: { label: 'низкий', tone: 'info' },
}

function formatDate(iso: string): string {
  const [year, month, day] = iso.split('-')
  return `${day}.${month}.${year}`
}

export default function Documents() {
  const [orders, setOrders] = useState<Order[] | null>(null)
  const [source, setSource] = useState('')
  const [error, setError] = useState<unknown>(null)
  const [selected, setSelected] = useState<Order | null>(null)

  const load = useCallback(() => {
    api
      .orders()
      .then((result) => {
        setOrders(result.orders)
        setSource(result.source)
        setError(null)
      })
      .catch(setError)
  }, [])

  useEffect(load, [load])

  useEffect(() => {
    if (!selected) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setSelected(null)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [selected])

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Документы 1С</h1>
          <div className="page-sub">
            Заказы производственного плана · только чтение · источник:{' '}
            <span className="mono">{source || '—'}</span>
          </div>
        </div>
        <Badge tone="info">режим чтения</Badge>
      </div>

      <Panel
        title="Открытые заказы"
        hint={source === 'stub' ? 'демо-данные stub-адаптера, не выгрузка 1С' : 'из 1С по HTTP-сервису'}
      >
        {error ? (
          <ErrorState
            message={error instanceof Error ? error.message : 'ошибка запроса'}
            onRetry={load}
          />
        ) : !orders ? (
          <SkeletonRows rows={5} />
        ) : orders.length === 0 ? (
          <EmptyState title="Заказов нет" hint="Открытые заказы появятся из 1С на этапе 4b." />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Заказ</th>
                  <th>Изделие</th>
                  <th className="num">Кол-во</th>
                  <th>Приоритет</th>
                  <th>Срок</th>
                  <th>Спецификация</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr
                    key={order.order_id}
                    onClick={() => setSelected(order)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td className="mono">{order.order_id}</td>
                    <td>{order.product}</td>
                    <td className="num">{order.qty}</td>
                    <td>
                      <Badge tone={PRIORITY[order.priority]?.tone ?? 'info'}>
                        {PRIORITY[order.priority]?.label ?? order.priority}
                      </Badge>
                    </td>
                    <td className="mono">{formatDate(order.due_date)}</td>
                    <td className="mono faint">{order.spec_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      {selected && (
        <>
          <div className="drawer-backdrop" onClick={() => setSelected(null)} />
          <aside className="drawer" role="dialog" aria-label={`Заказ ${selected.order_id}`}>
            <div className="panel-head">
              <div>
                <div className="panel-title">Заказ {selected.order_id}</div>
                <div className="panel-hint">только чтение · изменение в 1С запрещено</div>
              </div>
              <button className="btn btn-secondary" onClick={() => setSelected(null)}>
                Закрыть
              </button>
            </div>

            <table className="data">
              <tbody>
                <tr>
                  <td className="muted">Изделие</td>
                  <td>{selected.product}</td>
                </tr>
                <tr>
                  <td className="muted">Количество</td>
                  <td className="num">{selected.qty}</td>
                </tr>
                <tr>
                  <td className="muted">Приоритет</td>
                  <td>
                    <Badge tone={PRIORITY[selected.priority]?.tone ?? 'info'}>
                      {PRIORITY[selected.priority]?.label ?? selected.priority}
                    </Badge>
                  </td>
                </tr>
                <tr>
                  <td className="muted">Срок</td>
                  <td className="mono">{formatDate(selected.due_date)}</td>
                </tr>
                <tr>
                  <td className="muted">Спецификация</td>
                  <td className="mono">{selected.spec_id}</td>
                </tr>
              </tbody>
            </table>

            <div className="faint" style={{ fontSize: 12, marginTop: 16 }}>
              Позиции и суммы появятся после подключения HTTP-сервисов 1С (этап 4b). Сейчас
              показываются только поля stub-адаптера.
            </div>
          </aside>
        </>
      )}
    </>
  )
}
