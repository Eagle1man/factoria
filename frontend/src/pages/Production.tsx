import { getToken } from '../lib/api'
import { useTags, qualityOf } from '../lib/stream'
import { Badge, Panel, QualityBadge, formatNumber, formatTime } from '../components/ui'
import type { Quality, TagValue } from '../lib/api'

const LINES = ['L1', 'L2', 'L3'] as const

const TAGS = [
  { name: 'Running', label: 'Работа', unit: '' },
  { name: 'Speed.SP', label: 'Уставка', unit: 'rpm' },
  { name: 'Speed.PV', label: 'Обороты', unit: 'rpm' },
  { name: 'Temp.PV', label: 'Температура', unit: '°C' },
  { name: 'Load.Pct', label: 'Загрузка', unit: '%' },
  { name: 'Alarm.Code', label: 'Код аварии', unit: '' },
  { name: 'Recipe.ID', label: 'Рецепт', unit: '' },
] as const

function show(value: TagValue | undefined): string {
  if (!value || value.v === null || value.v === undefined) return '—'
  if (typeof value.v === 'number') return formatNumber(value.v, Number.isInteger(value.v) ? 0 : 1)
  if (typeof value.v === 'boolean') return value.v ? 'да' : 'нет'
  return String(value.v)
}

function LinePanel({
  line,
  values,
  quality,
}: {
  line: string
  values: Record<string, TagValue>
  quality: Quality
}) {
  const alarm = Number(values[`${line}.Alarm.Code`]?.v ?? 0)
  const running = Boolean(values[`${line}.Running`]?.v)
  const updated = formatTime(values[`${line}.Speed.PV`]?.ts)

  return (
    <Panel
      title={line}
      hint={`${running ? 'линия работает' : 'линия остановлена'} · обновлено ${updated}`}
      actions={
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {alarm !== 0 && <Badge tone="bad">авария {alarm}</Badge>}
          <QualityBadge quality={quality} />
        </div>
      }
    >
      <table className="data">
        <tbody>
          {TAGS.map((tag) => {
            const id = `${line}.${tag.name}`
            const value = values[id]
            const tagQuality = qualityOf(value)
            const dead = tagQuality === 'BAD'
            const stale = tagQuality === 'STALE'
            return (
              <tr key={id}>
                <td className="muted">
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    {tag.label}
                    {stale && <Badge tone="warn">устарело</Badge>}
                  </span>
                </td>
                <td
                  className="num"
                  title={value?.ts ? `обновлено ${formatTime(value.ts)}` : undefined}
                  style={dead ? { color: 'var(--ink-faint)' } : stale ? { color: 'var(--warning)' } : undefined}
                >
                  {dead ? 'нет данных' : show(value)}
                </td>
                <td className="faint">{tag.unit || '—'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </Panel>
  )
}

export default function Production() {
  const { values, seq, state } = useTags(getToken())

  const alarms = LINES.map((line) => ({
    line,
    code: Number(values[`${line}.Alarm.Code`]?.v ?? 0),
  })).filter((item) => item.code !== 0)

  const channel = state === 'open' ? 'канал открыт' : state === 'connecting' ? 'подключение…' : 'канал закрыт'

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Производство</h1>
          <div className="page-sub">Живые значения по WS · обновление не реже 100 мс · {channel}</div>
        </div>
        <div className="mono faint">seq {seq}</div>
      </div>

      {alarms.length > 0 && (
        <div className="panel" style={{ borderColor: 'var(--danger)', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Badge tone="bad">авария</Badge>
            <span className="muted">
              Активные аварии: {alarms.map((item) => `${item.line} — код ${item.code}`).join('; ')}
            </span>
          </div>
        </div>
      )}

      <div className="grid grid-lines">
        {LINES.map((line) => (
          <LinePanel
            key={line}
            line={line}
            values={values}
            quality={qualityOf(values[`${line}.Speed.PV`])}
          />
        ))}
      </div>

      <Panel
        title="Управление линиями"
        hint="команды появятся на этапе 4a — сейчас любая запись в контур запрещена"
      >
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {LINES.map((line) => (
            <div key={line} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span className="mono muted">{line}</span>
              <button
                className="btn btn-secondary"
                disabled
                title="этап 4a: POST /commands + подтверждение"
              >
                Пуск
              </button>
              <button
                className="btn btn-secondary"
                disabled
                title="этап 4a: POST /commands + подтверждение"
              >
                Стоп
              </button>
            </div>
          ))}
        </div>
      </Panel>
    </>
  )
}
