import { EmptyState, Panel } from '../components/ui'

export default function Stub({
  title,
  subtitle,
  stage,
  items,
}: {
  title: string
  subtitle: string
  stage: string
  items: string[]
}) {
  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">{title}</h1>
          <div className="page-sub">{subtitle}</div>
        </div>
        <span className="chip">{stage}</span>
      </div>

      <Panel>
        <EmptyState
          title={`Раздел появится на ${stage}`}
          hint="Экран не показывает выдуманных чисел: пока данных нет, здесь пусто."
        />
      </Panel>

      <Panel title="Что будет на экране">
        <ul className="muted" style={{ margin: 0, paddingLeft: 18, fontSize: 12, display: 'grid', gap: 6 }}>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Panel>
    </>
  )
}
