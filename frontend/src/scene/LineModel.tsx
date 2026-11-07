import { Html } from '@react-three/drei'
import { BINDINGS } from './bindings'
import Lathe from './Lathe'
import type { TagValue } from '../lib/api'

function tagFor(line: string, mode: 'spin' | 'heat' | 'visibility' | 'label'): string | undefined {
  return BINDINGS.find((binding) => binding.mesh.startsWith(`${line}.`) && binding.mode === mode)?.tag
}

function numeric(value: TagValue | undefined): number | null {
  return typeof value?.v === 'number' ? value.v : null
}

export default function LineModel({
  line,
  values,
  position,
}: {
  line: string
  values: Record<string, TagValue>
  position: [number, number, number]
}) {
  const spinTag = tagFor(line, 'spin')
  const heatTag = tagFor(line, 'heat')
  const visibilityTag = tagFor(line, 'visibility')

  const speed = spinTag ? numeric(values[spinTag]) ?? 0 : 0
  const temp = heatTag ? numeric(values[heatTag]) ?? 20 : 20
  const load = numeric(values[`${line}.Load.Pct`]) ?? 0
  const quality = spinTag ? values[spinTag]?.q ?? 'BAD' : 'BAD'
  const running = visibilityTag ? Boolean(values[visibilityTag]?.v) : false
  const alarm = Number(values[`${line}.Alarm.Code`]?.v ?? 0)
  const dead = quality !== 'GOOD'

  return (
    <group position={position}>
      <Lathe speed={speed} temp={temp} load={load} running={running} alarm={alarm} dead={dead} />
      <Html position={[0, 2.05, 0]} center distanceFactor={9} occlude={false}>
        <div className="scene-label">
          <b>{line}</b>
          <span>{dead ? 'нет данных' : `${Math.round(speed)} rpm · ${temp.toFixed(0)} °C · ${load.toFixed(0)} %`}</span>
        </div>
      </Html>
    </group>
  )
}
