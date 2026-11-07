import { useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { RoundedBox } from '@react-three/drei'
import * as THREE from 'three'

const PAINT = new THREE.Color('#46586b')
const PAINT_HOT = new THREE.Color('#b5543a')
const OFFLINE = new THREE.Color('#4a545e')

function stripeTexture(): THREE.CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = 256
  canvas.height = 32
  const ctx = canvas.getContext('2d')!
  ctx.fillStyle = '#0f151b'
  ctx.fillRect(0, 0, 256, 32)
  ctx.fillStyle = '#d9a520'
  for (let x = -32; x < 256; x += 48) {
    ctx.beginPath()
    ctx.moveTo(x, 32)
    ctx.lineTo(x + 24, 0)
    ctx.lineTo(x + 48, 0)
    ctx.lineTo(x + 24, 32)
    ctx.closePath()
    ctx.fill()
  }
  const texture = new THREE.CanvasTexture(canvas)
  texture.wrapS = THREE.RepeatWrapping
  texture.repeat.set(3, 1)
  return texture
}

export interface LatheProps {
  speed: number
  temp: number
  load: number
  running: boolean
  alarm: number
  dead: boolean
}

export default function Lathe({ speed, temp, running, alarm, dead }: LatheProps) {
  const chuck = useRef<THREE.Group>(null)
  const body = useRef<THREE.Group>(null)
  const beacon = useRef<THREE.Mesh>(null)
  const beaconLight = useRef<THREE.PointLight>(null)
  const blink = useRef(0)

  const heat = Math.min(1, Math.max(0, (temp - 20) / 100))
  const paint = useMemo(() => (dead ? OFFLINE.clone() : PAINT.clone()), [dead])
  const glow = dead ? 0 : Math.max(0, (temp - 45) / 75) * 0.5

  const stripes = useMemo(stripeTexture, [])

  const steel = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#c3d0dc', metalness: 0.85, roughness: 0.22 }),
    [],
  )
  const castIron = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#2a343f', metalness: 0.45, roughness: 0.65 }),
    [],
  )
  const dark = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#121a22', metalness: 0.3, roughness: 0.8 }),
    [],
  )
  const rubber = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#1d2a35', metalness: 0.1, roughness: 0.95 }),
    [],
  )
  const painted = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: paint,
        metalness: 0.35,
        roughness: 0.5,
        emissive: PAINT_HOT,
        emissiveIntensity: glow,
      }),
    [paint, glow],
  )

  useFrame((state, delta) => {
    if (chuck.current) {
      chuck.current.rotation.x += dead ? 0 : (speed / 1200) * delta * 22
    }
    if (body.current) {
      const shake = running && !dead ? Math.sin(state.clock.elapsedTime * 45) * 0.0016 : 0
      body.current.position.y = shake
    }
    if (beacon.current) {
      const material = beacon.current.material as THREE.MeshStandardMaterial
      blink.current += delta
      if (alarm !== 0) {
        const on = Math.sin(blink.current * 7) > 0
        material.emissiveIntensity = on ? 3 : 0.2
        material.color.set(on ? '#ef5350' : '#5a1f1f')
        if (beaconLight.current) beaconLight.current.intensity = on ? 2.4 : 0.2
      } else {
        material.emissiveIntensity = running ? 0.9 : 0.15
        material.color.set(running ? '#2fbf71' : '#33414d')
        if (beaconLight.current) beaconLight.current.intensity = running ? 0.6 : 0.05
      }
      beacon.current.visible = !dead
    }
  })

  return (
    <group ref={body}>
      {/* тумба и поддон */}
      <RoundedBox args={[3.0, 0.6, 1.1]} radius={0.04} smoothness={3} position={[0, 0.3, 0]} castShadow receiveShadow>
        <primitive object={painted} attach="material" />
      </RoundedBox>
      <mesh position={[0, 0.62, 0]} receiveShadow>
        <boxGeometry args={[3.16, 0.05, 1.2]} />
        <primitive object={dark} attach="material" />
      </mesh>
      {[
        [-1.38, 0.04, -0.46],
        [-1.38, 0.04, 0.46],
        [1.38, 0.04, -0.46],
        [1.38, 0.04, 0.46],
      ].map((position, index) => (
        <mesh key={index} position={position as [number, number, number]} castShadow>
          <cylinderGeometry args={[0.07, 0.08, 0.09, 12]} />
          <primitive object={dark} attach="material" />
        </mesh>
      ))}

      {/* станина */}
      <mesh position={[0, 0.73, 0]} castShadow receiveShadow>
        <boxGeometry args={[3.0, 0.18, 0.9]} />
        <primitive object={castIron} attach="material" />
      </mesh>
      <mesh position={[0, 0.83, 0.46]} rotation={[0, 0, 0]}>
        <boxGeometry args={[3.0, 0.04, 0.03]} />
        <primitive object={steel} attach="material" />
      </mesh>

      {/* жёлто-чёрная полоса на тумбе */}
      <mesh position={[0, 0.42, 0.556]}>
        <planeGeometry args={[2.7, 0.1]} />
        <meshStandardMaterial map={stripes} roughness={0.7} metalness={0.1} />
      </mesh>

      {/* передняя бабка */}
      <RoundedBox args={[0.8, 0.82, 0.95]} radius={0.03} smoothness={3} position={[-1.0, 1.23, 0]} castShadow>
        <primitive object={painted} attach="material" />
      </RoundedBox>
      <mesh position={[-0.58, 1.23, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.24, 0.26, 0.22, 24]} />
        <primitive object={castIron} attach="material" />
      </mesh>

      {/* патрон с кулачками и заготовкой — вращается по Speed.PV */}
      <group ref={chuck} position={[-0.44, 1.23, 0]}>
        <mesh rotation={[0, 0, Math.PI / 2]} castShadow>
          <cylinderGeometry args={[0.32, 0.32, 0.16, 32]} />
          <primitive object={steel} attach="material" />
        </mesh>
        <mesh position={[0.02, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.09, 0.09, 0.18, 20]} />
          <primitive object={dark} attach="material" />
        </mesh>
        {[0, 1, 2].map((index) => {
          const angle = (index * Math.PI * 2) / 3
          return (
            <mesh
              key={index}
              position={[0.02, Math.cos(angle) * 0.2, Math.sin(angle) * 0.2]}
              rotation={[angle, 0, 0]}
              castShadow
            >
              <boxGeometry args={[0.2, 0.1, 0.07]} />
              <primitive object={steel} attach="material" />
            </mesh>
          )
        })}
        {/* заготовка */}
        <mesh position={[0.62, 0, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
          <cylinderGeometry args={[0.1, 0.1, 1.25, 24]} />
          <primitive object={steel} attach="material" />
        </mesh>
        <mesh position={[0.62, 0.095, 0]}>
          <boxGeometry args={[1.2, 0.012, 0.02]} />
          <primitive object={dark} attach="material" />
        </mesh>
      </group>

      {/* задняя бабка */}
      <RoundedBox args={[0.55, 0.5, 0.78]} radius={0.03} smoothness={3} position={[1.05, 1.07, 0]} castShadow>
        <primitive object={castIron} attach="material" />
      </RoundedBox>
      <mesh position={[0.72, 1.07, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.06, 0.06, 0.5, 16]} />
        <primitive object={steel} attach="material" />
      </mesh>
      <mesh position={[1.34, 1.07, 0]} rotation={[0, Math.PI / 2, 0]} castShadow>
        <torusGeometry args={[0.16, 0.02, 10, 24]} />
        <primitive object={steel} attach="material" />
      </mesh>
      {[0, 1, 2].map((index) => (
        <mesh
          key={index}
          position={[1.34, 1.07, 0]}
          rotation={[(index * Math.PI) / 3, 0, 0]}
        >
          <boxGeometry args={[0.02, 0.3, 0.02]} />
          <primitive object={steel} attach="material" />
        </mesh>
      ))}

      {/* суппорт и резцедержка */}
      <mesh position={[0.12, 0.9, 0]} castShadow>
        <boxGeometry args={[0.55, 0.16, 0.85]} />
        <primitive object={castIron} attach="material" />
      </mesh>
      <mesh position={[0.12, 1.0, 0]} castShadow>
        <boxGeometry args={[0.4, 0.12, 0.55]} />
        <primitive object={castIron} attach="material" />
      </mesh>
      <mesh position={[0.12, 1.12, 0]} castShadow>
        <boxGeometry args={[0.18, 0.2, 0.24]} />
        <primitive object={dark} attach="material" />
      </mesh>
      <mesh position={[0.02, 1.22, 0.02]} castShadow>
        <boxGeometry args={[0.06, 0.05, 0.2]} />
        <meshStandardMaterial color="#d9c27a" metalness={0.9} roughness={0.25} />
      </mesh>
      <mesh position={[0.12, 1.0, 0.52]} rotation={[Math.PI / 2, 0, 0]} castShadow>
        <torusGeometry args={[0.12, 0.018, 10, 20]} />
        <primitive object={steel} attach="material" />
      </mesh>

      {/* пульт */}
      <group position={[0.72, 1.42, 0.42]} rotation={[-0.28, 0, 0]}>
        <RoundedBox args={[0.56, 0.34, 0.08]} radius={0.02} smoothness={2} castShadow>
          <primitive object={dark} attach="material" />
        </RoundedBox>
        <mesh position={[0, 0.02, 0.045]}>
          <planeGeometry args={[0.38, 0.18]} />
          <meshStandardMaterial color="#0d1a26" emissive="#2b7fbf" emissiveIntensity={0.8} />
        </mesh>
        {[-0.18, -0.06, 0.06, 0.18].map((x, index) => (
          <mesh key={index} position={[x, -0.12, 0.05]} rotation={[Math.PI / 2, 0, 0]}>
            <cylinderGeometry args={[0.018, 0.018, 0.02, 12]} />
            <meshStandardMaterial
              color={index === 3 ? '#ef5350' : '#8fa3b5'}
              emissive={index === 3 ? '#ef5350' : '#000000'}
              emissiveIntensity={index === 3 ? 1.2 : 0}
            />
          </mesh>
        ))}
      </group>

      {/* маячок */}
      <mesh position={[0.72, 1.66, 0.42]}>
        <cylinderGeometry args={[0.05, 0.06, 0.06, 12]} />
        <primitive object={dark} attach="material" />
      </mesh>
      <mesh ref={beacon} position={[0.72, 1.72, 0.42]}>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshStandardMaterial color="#33414d" emissive="#33414d" emissiveIntensity={0.2} />
      </mesh>
      <pointLight ref={beaconLight} position={[0.72, 1.78, 0.42]} color="#ef5350" intensity={0.1} distance={1.6} />

      {/* шланг СОЖ */}
      <mesh castShadow>
        <tubeGeometry
          args={[
            new THREE.CatmullRomCurve3([
              new THREE.Vector3(-0.75, 1.65, 0.3),
              new THREE.Vector3(-0.4, 1.78, 0.42),
              new THREE.Vector3(0.0, 1.55, 0.46),
              new THREE.Vector3(0.12, 1.32, 0.34),
            ]),
            32,
            0.018,
            8,
            false,
          ]}
        />
        <primitive object={rubber} attach="material" />
      </mesh>

      {/* кабель-канал от пульта к бабке */}
      <mesh>
        <tubeGeometry
          args={[
            new THREE.CatmullRomCurve3([
              new THREE.Vector3(0.45, 1.4, 0.44),
              new THREE.Vector3(0.1, 1.52, 0.5),
              new THREE.Vector3(-0.4, 1.58, 0.42),
              new THREE.Vector3(-0.62, 1.5, 0.3),
            ]),
            24,
            0.014,
            6,
            false,
          ]}
        />
        <primitive object={rubber} attach="material" />
      </mesh>
    </group>
  )
}
