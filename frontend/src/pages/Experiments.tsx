import { useCallback, useEffect, useState } from 'react'
import { api, type SimCompare, type SimRun, type SimScenario } from '../lib/api'
import { useAuth } from '../lib/auth'
import {
  Badge,
  ErrorState,
  Panel,
  SkeletonRows,
  formatDateTime,
  formatNumber,
} from '../components/ui'

const METRIC_LABEL: Record<string, string> = {
  output_index: 'Выпуск, у.е.',
  max_temp: 'Макс. температура, °C',
  avg_load: 'Средняя загрузка, %',
  uptime_pct: 'Время в работе, %',
  alarms: 'Аварии',
}

export default function Experiments() {
  const { role } = useAuth()
  const [scenarios, setScenarios] = useState<SimScenario[]>([])
  const [runs, setRuns] = useState<SimRun[] | null>(null)
  const [scenario, setScenario] = useState('nominal')
  const [seed, setSeed] = useState(42)
  const [horizon, setHorizon] = useState(120)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [selected, setSelected] = useState<number[]>([])
  const [comparison, setComparison] = useState<SimCompare | null>(null)

  const load = useCallback(() => {
    Promise.all([api.simScenarios(), api.simRuns(20)])
      .then(([scenarioData, runData]) => {
        setScenarios(scenarioData.scenarios)
        setRuns(runData.runs)
        setError(null)
      })
      .catch(setError)
  }, [])

  useEffect(load, [load])

  useEffect(() => {
    if (selected.length !== 2) {
      setComparison(null)
      return
    }
    api
      .compareSimRuns(selected[0], selected[1])
      .then(setComparison)
      .catch(() => setComparison(null))
  }, [selected])

  async function run() {
    setBusy(true)
    try {
      await api.createSimRun(scenario, seed, horizon)
      setSelected([])
      load()
    } catch (problem) {
      setError(problem)
    } finally {
      setBusy(false)
    }
  }

  function toggle(id: number) {
    setSelected((previous) => {
      if (previous.includes(id)) return previous.filter((item) => item !== id)
      return [...previous, id].slice(-2)
    })
    setComparison(null)
  }

  const canRun = role === 'production_specialist' || role === 'technologist'
  const current = scenarios.find((item) => item.name === scenario)

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Эксперименты</h1>
          <div className="page-sub">
            Детерминированная симуляция линии · одинаковый seed даёт одинаковый результат
          </div>
        </div>
        <div className="mono faint">{runs ? `прогонов: ${runs.length}` : '—'}</div>
      </div>

      {error != null && (
        <Panel>
          <ErrorState
            message={error instanceof Error ? error.message : 'ошибка запроса'}
            onRetry={load}
          />
        </Panel>
      )}

      <Panel
        title="Запуск"
        hint={current?.description ?? 'выберите сценарий'}
        actions={
          canRun ? (
            <button className="btn btn-primary" onClick={run} disabled={busy}>
              {busy ? 'Считаю…' : 'Запустить'}
            </button>
          ) : null
        }
      >
        <div className="form-row">
          <label className="field">
            <span>Сценарий</span>
            <select
              className="input"
              value={scenario}
              onChange={(event) => setScenario(event.target.value)}
            >
              {scenarios.map((item) => (
                <option key={item.name} value={item.name}>
                  {item.title}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Seed</span>
            <input
              className="input"
              type="number"
              min={0}
              value={seed}
              onChange={(event) => setSeed(Number(event.target.value))}
            />
          </label>
          <label className="field">
            <span>Горизонт, c</span>
            <input
              className="input"
              type="number"
              min={10}
              max={3600}
              step={10}
              value={horizon}
              onChange={(event) => setHorizon(Number(event.target.value))}
            />
          </label>
        </div>
        <div className="faint" style={{ fontSize: 12, marginTop: 8 }}>
          Прогон считается на сервере и сохраняется с хешем воспроизводимости.
          Данные симуляции — не факт с производства.
        </div>
      </Panel>

      <Panel
        title="История прогонов"
        hint="выберите два прогона, чтобы сравнить метрики"
      >
        {!runs ? (
          <SkeletonRows rows={5} />
        ) : runs.length === 0 ? (
          <div className="muted" style={{ fontSize: 12 }}>
            Прогонов пока нет. Выберите сценарий и нажмите «Запустить».
          </div>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Время</th>
                  <th>Сценарий</th>
                  <th className="num">Seed</th>
                  <th className="num">Горизонт</th>
                  <th className="num">Выпуск</th>
                  <th className="num">Макс. T</th>
                  <th className="num">Загрузка</th>
                  <th className="num">В работе</th>
                  <th className="num">Аварии</th>
                  <th>Хеш</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((item) => (
                  <tr
                    key={item.id}
                    className={selected.includes(item.id) ? 'row-selected' : undefined}
                    onClick={() => toggle(item.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td className="mono">
                      {item.created_at ? formatDateTime(item.created_at) : '—'}
                    </td>
                    <td>{item.scenario}</td>
                    <td className="num">{item.seed}</td>
                    <td className="num">{item.horizon_s} c</td>
                    <td className="num">{formatNumber(item.metrics.output_index, 1)}</td>
                    <td className="num">{formatNumber(item.metrics.max_temp, 1)}</td>
                    <td className="num">{formatNumber(item.metrics.avg_load, 1)}</td>
                    <td className="num">{formatNumber(item.metrics.uptime_pct, 1)}</td>
                    <td className="num">
                      {item.metrics.alarms > 0 ? (
                        <Badge tone="bad">{item.metrics.alarms}</Badge>
                      ) : (
                        <span className="faint">0</span>
                      )}
                    </td>
                    <td className="mono faint">{item.repro_hash}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <Panel
        title="Сравнение прогонов"
        hint={
          selected.length === 2 ? 'раньше → позже по времени' : 'выберите два прогона в таблице'
        }
      >
        {selected.length !== 2 ? (
          <div className="muted" style={{ fontSize: 12 }}>
            Отметьте две строки — покажу разницу по выпуску, температуре, загрузке,
            времени в работе и авариям.
          </div>
        ) : !comparison ? (
          <SkeletonRows rows={2} />
        ) : (
          <>
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>Показатель</th>
                    <th className="num">
                      Прогон {comparison.from.id} ({comparison.from.scenario}, seed{' '}
                      {comparison.from.seed})
                    </th>
                    <th className="num">
                      Прогон {comparison.to.id} ({comparison.to.scenario}, seed{' '}
                      {comparison.to.seed})
                    </th>
                    <th className="num">Δ</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(METRIC_LABEL).map(([key, label]) => {
                    const delta = comparison.delta[key] ?? 0
                    const left = (comparison.metrics.from as unknown as Record<string, number>)[key] ?? 0
                    const right = (comparison.metrics.to as unknown as Record<string, number>)[key] ?? 0
                    const tone =
                      delta === 0
                        ? 'var(--ink-muted)'
                        : delta > 0
                          ? 'var(--success)'
                          : 'var(--danger)'
                    return (
                      <tr key={key}>
                        <td className="muted">{label}</td>
                        <td className="num">
                          {formatNumber(left, 2)}
                        </td>
                        <td className="num">
                          {formatNumber(right, 2)}
                        </td>
                        <td className="num" style={{ color: tone }}>
                          {delta > 0 ? '+' : ''}
                          {formatNumber(delta, 2)}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <div className="faint" style={{ fontSize: 12, marginTop: 8 }}>
              {comparison.same_repro
                ? 'Хеши совпали: прогоны воспроизводимы при одинаковых входных данных.'
                : 'Хеши разные: сценарий, seed или горизонт отличаются.'}
            </div>
          </>
        )}
      </Panel>
    </>
  )
}
