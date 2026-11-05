import { Suspense, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import { Grid, OrbitControls } from '@react-three/drei'
import { getToken } from '../lib/api'
import { useTags, qualityOf } from '../lib/stream'
import { Badge, ErrorState, Panel, QualityBadge, SkeletonRows } from '../components/ui'
import LineModel from '../scene/LineModel'

const LINES: Array<'L1' | 'L2' | 'L3'> = ['L1', 'L2', 'L3']
const POSITIONS: Record<string, [number, number, number]> = {
  L1: [-3.6, 0, 0],
  L2: [0, 0, 0],
  L3: [3.6, 0, 0],
}

function webglAvailable(): boolean {
  try {
    const canvas = document.createElement('canvas')
    return Boolean(
      canvas.getContext('webgl2') || canvas.getContext('webgl') || canvas.getContext('experimental-webgl'),
    )
  } catch {
    return false
  }
}

export default function Scene() {
  const { values, state } = useTags(getToken())
  const supported = useMemo(webglAvailable, [])
  const dead = LINES.filter((line) => qualityOf(values[`${line}.Speed.PV`]) !== 'GOOD').length

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">3D-сцена</h1>
          <div className="page-sub">
            Ротор — по оборотам, корпус — по температуре · {state === 'open' ? 'живые данные' : 'ожидание канала'}
          </div>
        </div>
        <div className="mono faint">{dead === 0 ? 'все линии в норме' : `нет данных: ${dead}`}</div>
      </div>

      {!supported ? (
        <Panel>
          <ErrorState
            message="браузер не дал WebGL-контекст. Сцена недоступна, но данные линий остаются на экране «Производство»."
            code="WEBGL_UNAVAILABLE"
          />
        </Panel>
      ) : (
        <div className="scene-layout">
          <div className="scene-canvas">
            <Canvas camera={{ position: [0, 3.8, 8.4], fov: 40 }} dpr={[1, 2]} shadows>
              <color attach="background" args={['#0b1117']} />
              <hemisphereLight args={['#9fb6cc', '#0b1117', 0.75]} />
              <ambientLight intensity={0.35} />
              <directionalLight position={[6, 10, 6]} intensity={2.0} castShadow />
              <directionalLight position={[-6, 6, -4]} intensity={0.5} />
              <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
                <planeGeometry args={[36, 36]} />
                <meshStandardMaterial color="#0e1720" roughness={1} metalness={0} />
              </mesh>

              <Suspense fallback={null}>
                {LINES.map((line) => (
                  <LineModel key={line} line={line} values={values} position={POSITIONS[line]} />
                ))}
                <Grid
                  position={[0, 0, 0]}
                  args={[24, 24]}
                  cellSize={0.6}
                  cellThickness={0.5}
                  cellColor="#1c2a38"
                  sectionSize={3}
                  sectionThickness={1}
                  sectionColor="#2a3d50"
                  fadeDistance={26}
                  fadeStrength={1}
                  infiniteGrid={false}
                />
              </Suspense>

              <OrbitControls
                target={[0, 0.8, 0]}
                enablePan={false}
                minDistance={4}
                maxDistance={16}
                maxPolarAngle={Math.PI / 2.05}
              />
            </Canvas>
          </div>

          <div className="scene-side">
            <Panel title="Легенда">
              <div className="scene-legend">
                <div>
                  <span className="scene-swatch" style={{ background: '#2b3a46' }} />
                  холодный корпус
                </div>
                <div>
                  <span className="scene-swatch" style={{ background: '#e2663a' }} />
                  нагрев по Temp.PV
                </div>
                <div>
                  <span className="scene-swatch" style={{ background: '#2fbf71' }} />
                  линия работает
                </div>
                <div>
                  <span className="scene-swatch" style={{ background: '#ef5350' }} />
                  авария, мигает
                </div>
                <div>
                  <span className="scene-swatch" style={{ background: '#3a444f' }} />
                  серый — нет данных
                </div>
              </div>
            </Panel>

            <Panel title="Линии" hint="качество данных">
              {Object.keys(values).length === 0 ? (
                <SkeletonRows rows={3} />
              ) : (
                <div className="scene-list">
                  {LINES.map((line) => {
                    const quality = qualityOf(values[`${line}.Speed.PV`])
                    const alarm = Number(values[`${line}.Alarm.Code`]?.v ?? 0)
                    return (
                      <div key={line} className="scene-row">
                        <span className="mono">{line}</span>
                        {alarm !== 0 ? <Badge tone="bad">авария {alarm}</Badge> : <QualityBadge quality={quality} />}
                      </div>
                    )
                  })}
                </div>
              )}
              <div className="faint" style={{ fontSize: 12, marginTop: 12 }}>
                Серая модель означает, что значение устарело или недоступно: последнее известное
                число не показывается.
              </div>
            </Panel>
          </div>
        </div>
      )}
    </>
  )
}
