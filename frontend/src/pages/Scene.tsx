import { Suspense, useMemo, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { ContactShadows, Environment, Grid, Lightformer, OrbitControls } from '@react-three/drei'
import { getToken } from '../lib/api'
import { useTags, qualityOf } from '../lib/stream'
import { Badge, ErrorState, Panel, QualityBadge, SkeletonRows } from '../components/ui'
import LineModel from '../scene/LineModel'

const LINES: Array<'L1' | 'L2' | 'L3'> = ['L1', 'L2', 'L3']
const POSITIONS: Record<string, [number, number, number]> = {
  L1: [-3.05, 0, 0],
  L2: [0, 0, 0],
  L3: [3.05, 0, 0],
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
  const [inspect, setInspect] = useState(false)
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
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className={inspect ? 'btn btn-primary' : 'btn btn-secondary'} onClick={() => setInspect((v) => !v)}>
            {inspect ? 'Инспекция: авто-облёт' : 'Инспекция'}
          </button>
          <div className="mono faint">{dead === 0 ? 'все линии в норме' : `нет данных: ${dead}`}</div>
        </div>
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
            <Canvas
              camera={{ position: [0, 2.8, 8.6], fov: 42 }}
              dpr={[1, 2]}
              shadows
              gl={{ antialias: true }}
            >
              <color attach="background" args={['#0b1117']} />
              <hemisphereLight args={['#9fb6cc', '#0b1117', 0.5]} />
              <ambientLight intensity={0.25} />
              <directionalLight
                position={[5, 9, 5]}
                intensity={3.0}
                castShadow
                shadow-mapSize={[2048, 2048]}
                shadow-bias={-0.0005}
              />
              <directionalLight position={[-7, 5, -4]} intensity={0.8} color="#7fa6c9" />
              <directionalLight position={[0, 4, -8]} intensity={0.9} color="#3ea6ff" />

              <Environment resolution={128} frames={1}>
                <Lightformer intensity={2.2} position={[0, 5, 2]} scale={[8, 3, 1]} color="#cfe3f5" />
                <Lightformer intensity={1.2} position={[-5, 2, 3]} scale={[4, 2, 1]} color="#8fb6d9" />
                <Lightformer intensity={0.8} position={[5, 3, -3]} scale={[4, 2, 1]} color="#3e6f96" />
              </Environment>

              <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
                <planeGeometry args={[40, 40]} />
                <meshStandardMaterial color="#0e1720" roughness={1} metalness={0} />
              </mesh>

              <ContactShadows
                position={[0, 0.005, 0]}
                opacity={0.55}
                scale={24}
                blur={2.2}
                far={5}
                resolution={512}
                color="#000000"
              />

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
                target={[0, 1.05, 0]}
                enablePan={false}
                minDistance={4}
                maxDistance={14}
                maxPolarAngle={Math.PI / 2.05}
                autoRotate={inspect}
                autoRotateSpeed={0.7}
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
