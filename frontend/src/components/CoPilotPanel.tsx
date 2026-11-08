import { useEffect, useMemo, useState } from 'react'
import { api, type ShopTemplate } from '../lib/api'
import { useAuth } from '../lib/auth'
import { Badge, Panel } from './ui'

type LineLive = {
  running?: boolean | null
  load?: number | null
  alarm?: number | null
  temp?: number | null
  speedSp?: number | null
  quality?: string
}

function rid(prefix: string): string {
  const rand = Math.random().toString(36).slice(2, 10)
  return `${prefix}-${Date.now().toString(36)}-${rand}`.slice(0, 39)
}

export default function CoPilotPanel({
  template,
  lineLive,
}: {
  template: ShopTemplate
  lineLive: Record<string, LineLive>
}) {
  const { role, userId } = useAuth()
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<{ tone: 'good' | 'warn' | 'bad'; text: string } | null>(null)
  const [llm, setLlm] = useState<{ provider: string; reachable: boolean; detail?: string } | null>(null)

  useEffect(() => {
    let alive = true
    api
      .health()
      .then((h) => alive && setLlm(h.llm ?? null))
      .catch(() => {})
    return () => {
      alive = false
    }
  }, [])

  const bLine = template.bottleneck_line_id ?? 'L1'
  const live = lineLive[bLine] ?? {}
  const alarm = Number(live.alarm ?? 0)
  const load = typeof live.load === 'number' ? live.load : null
  const temp = typeof live.temp === 'number' ? live.temp : null
  const sp = typeof live.speedSp === 'number' ? live.speedSp : null

  const analysis = useMemo(() => {
    const pressure = load != null ? Math.round(load) : null
    const hot = temp != null && temp > 75
    const high = pressure != null && pressure > 90
    const step1 = `Участок ${template.bottleneck_node_id} (${bLine}): ${
      alarm !== 0 ? `активен код аварии ${alarm}` : 'аварийного кода нет'
    }${pressure != null ? `, загрузка ${pressure}%` : ', загрузка не подтверждена'}${
      temp != null ? `, температура ${temp.toFixed(1)} °C` : ''
    }. Основание: живые теги L1-L3 + описание шаблона.`
    const step2 =
      high || hot
        ? `Риск перегруза/перегрева: рекомендуется снизить уставку скорости на 10–15% и перепроверить состояние линии до изменения.`
        : `Признаков критического перегруза по доступным сигналам нет. Можно рассмотреть плавное изменение уставки только после проверки оператором.`
    const targetSp =
      sp != null ? Math.max(0, Math.round(sp * (high || hot ? 0.85 : 0.95))) : high || hot ? 500 : 650
    const step3 = `Действие с записью в контур (если выбрано): \`set_setpoint\` для ${bLine}, целевая уставка ${targetSp} rpm — только через очередь согласований (A1), с комментарием и проверкой последствий. AGV/наряд 1С:ТОиР — вне автоматического транспорта, оформляются вручную/экспортом.`
    return { step1, step2, step3, targetSp, high: high || hot }
  }, [template, bLine, alarm, load, temp, sp])

  async function draftSetpoint() {
    if (!userId) {
      setMessage({ tone: 'bad', text: 'Не удалось определить пользователя.' })
      return
    }
    setBusy(true)
    setMessage(null)
    try {
      const command_id = rid('cmd')
      const correlation_id = rid('cor')
      const result = await api.submitCommand({
        command_id,
        type: 'set_setpoint',
        target: { line_id: bLine },
        params: { setpoint_value: analysis.targetSp },
        requested_by: { kind: 'human', id: userId },
        correlation_id,
        evidence: [
          `template:${template.id}`,
          `bottleneck:${template.bottleneck_node_id}`,
          `load:${load ?? 'na'}`,
          `alarm:${alarm}`,
        ],
      })
      setMessage({
        tone: 'good',
        text: `Запрос создан: ${result.command_id} · статус ${result.status}${
          result.status === 'AWAITING_APPROVAL' ? ' (ожидает согласования на вкладке «Согласования»)' : ''
        }.`,
      })
    } catch (e) {
      setMessage({
        tone: 'bad',
        text: e instanceof Error ? e.message : 'Не удалось создать запрос (проверьте контракт/роль/данные).',
      })
    } finally {
      setBusy(false)
    }
  }

  const canDraft = role === 'operator' || role === 'lead' || role === 'admin'

  return (
    <Panel
      title="Co-Pilot (анализ узкого места)"
      hint={
        llm && llm.provider !== 'none' && llm.reachable
          ? `LLM: ${llm.provider} (доступен); tool-вызовы/агент подключаются отдельно. Действия — через согласование (A1).`
          : `детерминированный режим${llm && llm.provider !== 'none' ? ` (LLM ${llm.provider}: ${llm.detail ?? 'недоступен'})` : ''}; без прямой записи в 1C/PLC, действия — через A1`
      }
    >
      <div style={{ display: 'grid', gap: 10 }}>
        <div className="panel" style={{ padding: 10 }}>
          <div style={{ marginBottom: 4 }}>
            <Badge tone="info">Шаг 1</Badge> <span className="muted">Анализ состояния</span>
          </div>
          <div style={{ fontSize: 13 }}>{analysis.step1}</div>
        </div>
        <div className="panel" style={{ padding: 10 }}>
          <div style={{ marginBottom: 4 }}>
            <Badge tone={analysis.high ? 'warn' : 'info'}>Шаг 2</Badge> <span className="muted">Рекомендация</span>
          </div>
          <div style={{ fontSize: 13 }}>{analysis.step2}</div>
        </div>
        <div className="panel" style={{ padding: 10 }}>
          <div style={{ marginBottom: 4 }}>
            <Badge tone="info">Шаг 3</Badge> <span className="muted">Действие и границы</span>
          </div>
          <div style={{ fontSize: 13 }}>{analysis.step3}</div>
        </div>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <button className="btn btn-primary" onClick={draftSetpoint} disabled={busy || !canDraft}>
            {busy ? 'Создание…' : `Подготовить согласование: уставка ${bLine} → ${analysis.targetSp} rpm`}
          </button>
          <span className="faint" style={{ fontSize: 12 }}>
            создаёт <span className="mono">set_setpoint</span> (A1); исполнитель подтверждает в «Согласованиях»
          </span>
        </div>
        {!canDraft && (
          <div className="faint" style={{ fontSize: 12 }}>
            Создание запроса доступно ролям operator/lead/admin (текущая: {role ?? '—'}).
          </div>
        )}
        <div className="panel" style={{ padding: 10, borderStyle: 'dashed' }}>
          <div className="muted" style={{ fontSize: 12 }}>
            <strong>Перенаправить AGV / наряд 1С:ТОиР</strong> — не выполняется автоматически (нет безопасного транспорта в
            этом контуре). Действие: сформировать наряд вручную или использовать экспорт XML; запись в 1C/оборудование
            агентом запрещена.
          </div>
        </div>
        {message && (
          <div className="panel" style={{ borderColor: message.tone === 'bad' ? 'var(--danger)' : message.tone === 'good' ? 'var(--success)' : 'var(--warning)' }}>
            <span className="muted">{message.text}</span>
          </div>
        )}
      </div>
    </Panel>
  )
}