import { useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { Html } from '@react-three/drei'
import * as THREE from 'three'
import { BINDINGS } from './bindings'
import type { TagValue } from '../lib/api'

function tagFor(line: string, mode: 'spin' | 'heat' | 'visibility' | 'label'): string | undefined {
  return BINDINGS.find((binding) => binding.mesh.startsWith(`${line}.`) && binding.mode === mode)?.tag
}

function numeric(value: TagValue | undefined): number | null {
  return typeof value?.v === 'number' ? value.v : null
}

const COLD = new THREE.Color('#4a5f73')
const HOT = new THREE.Color('#e2663a')
const OFFLINE = new THREE.Color('#46505b')

export default function LineModel({
  line,
  values,
  position,
}: {
  line: string
  values: Record<string, TagValue>
  position: [number, number, number]
}) {
  const rotor = useRef<THREE.Group>(null)
  const indicator = useRef<THREE.Mesh>(null)
  const blink = useRef(0)

  const spinTag = tagFor(line, 'spin')
  const heatTag = tagFor(line, 'heat')
  const visibilityTag = tagFor(line, 'visibility')

  const speed = spinTag ? numeric(values[spinTag]) ?? 0 : 0
  const temp = heatTag ? numeric(values[heatTag]) ?? 20 : 20
  const quality = spinTag ? values[spinTag]?.q ?? 'BAD' : 'BAD'
  const running = visibilityTag ? Boolean(values[visibilityTag]?.v) : false
  const alarm = Number(values[`${line}.Alarm.Code`]?.v ?? 0)
  const dead = quality !== 'GOOD'

  const bodyColor = useMemo(() => {
    if (dead) return OFFLINE.clone()
    const ratio = THREE.MathUtils.clamp((temp - 20) / 100, 0, 1)
    return COLD.clone().lerp(HOT, ratio)
  }, [dead, temp])

  const bodyGlow = dead ? 0 : THREE.MathUtils.clamp((temp - 20) / 100, 0, 1) * 0.45

  useFrame((state, delta) => {
    if (rotor.current) {
      const target = dead ? 0 : speed / 1200
      rotor.current.rotation.y += delta * target * 14
    }
    if (indicator.current) {
      const material = indicator.current.material as THREE.MeshStandardMaterial
      blink.current += delta
      if (alarm !== 0) {
        const on = Math.sin(blink.current * 6) > 0
        material.emissiveIntensity = on ? 2.2 : 0.15
        material.color.set(on ? '#ef5350' : '#5a1f1f')
      } else {
        material.emissiveIntensity = running ? 1.2 : 0.15
        material.color.set(running ? '#2fbf71' : '#33414d')
      }
      if (indicator.current) indicator.current.visible = !dead
    }
    void state
  })

  return (
    <group position={position}>
      {/* основание */}
      <mesh position={[0, 0.1, 0]} receiveShadow>
        <boxGeometry args={[2.2, 0.2, 1.6]} />
        <meshStandardMaterial color="#151f2a" roughness={0.9} metalness={0.1} />
      </mesh>

      {/* корпус: цвет = температура, серый = нет данных */}
      <mesh position={[0, 0.75, 0]} castShadow>
        <boxGeometry args={[1.8, 1.1, 1.3]} />
        <meshStandardMaterial
          color={bodyColor}
          emissive={HOT}
          emissiveIntensity={bodyGlow}
          roughness={0.5}
          metalness={0.25}
        />
      </mesh>

      {/* ротор: вращается по Speed.PV */}
      <group ref={rotor} position={[0, 0.75, 0]}>
        <mesh rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.11, 0.11, 2.25, 14]} />
          <meshStandardMaterial color="#c3d0dc" metalness={0.75} roughness={0.25} />
        </mesh>
        {[0, 1, 2, 3].map((index) => (
          <mesh key={index} rotation={[0, (index * Math.PI) / 2, 0]}>
            <boxGeometry args={[0.05, 0.62, 0.3]} />
            <meshStandardMaterial color="#9fb2c4" metalness={0.65} roughness={0.3} />
          </mesh>
        ))}
        <mesh position={[1.12, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.2, 0.2, 0.08, 16]} />
          <meshStandardMaterial color="#d6e2ee" metalness={0.8} roughness={0.2} />
        </mesh>
        <mesh position={[-1.12, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.2, 0.2, 0.08, 16]} />
          <meshStandardMaterial color="#d6e2ee" metalness={0.8} roughness={0.2} />
        </mesh>
      </group>

      {/* индикатор: работа / авария / нет данных */}
      <mesh ref={indicator} position={[0, 1.45, 0]}>
        <sphereGeometry args={[0.14, 16, 16]} />
        <meshStandardMaterial color="#33414d" emissive="#33414d" emissiveIntensity={0.2} />
      </mesh>

      <Html position={[0, 1.85, 0]} center distanceFactor={10} occlude={false}>
        <div className="scene-label">
          <b>{line}</b>
          <span>{dead ? 'нет данных' : `${Math.round(speed)} rpm · ${temp.toFixed(0)} °C`}</span>
        </div>
      </Html>
    </group>
  )
}
