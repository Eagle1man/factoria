import { useEffect, useRef } from 'react'
import type { ShopTemplate } from '../lib/api'

type LineLive = {
  running?: boolean | null
  load?: number | null
  alarm?: number | null
  quality?: string
}

function statusColor(status: string): string {
  if (status === 'BOTTLENECK') return '#ef5350'
  if (status === 'WARN_QUEUE') return '#f2b544'
  if (status === 'RUNNING') return '#2fbf71'
  return '#5c6b7d'
}

export default function FlowCanvas({
  template,
  lineLive,
}: {
  template: ShopTemplate
  lineLive: Record<string, LineLive>
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const wrapRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const wrap = wrapRef.current
    if (!canvas || !wrap) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let raf = 0
    let part = 0

    const resize = () => {
      const w = Math.max(320, Math.floor(wrap.clientWidth))
      const h = 280
      const dpr = window.devicePixelRatio || 1
      canvas.width = Math.floor(w * dpr)
      canvas.height = Math.floor(h * dpr)
      canvas.style.width = `${w}px`
      canvas.style.height = `${h}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      return { w, h }
    }

    const render = () => {
      const { w, h } = resize()
      ctx.clearRect(0, 0, w, h)

      // subtle grid
      ctx.strokeStyle = 'rgba(62, 166, 255, 0.08)'
      ctx.lineWidth = 1
      for (let x = 0; x < w; x += 28) {
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, h)
        ctx.stroke()
      }

      const stations = template.stations
      const n = Math.max(1, stations.length)
      const pad = 36
      const yLine = Math.floor(h * 0.62)
      const span = Math.max(120, w - pad * 2)
      const step = span / Math.max(1, n - 1)

      // conveyor
      ctx.strokeStyle = '#223041'
      ctx.lineWidth = 14
      ctx.lineCap = 'round'
      ctx.beginPath()
      ctx.moveTo(pad, yLine)
      ctx.lineTo(pad + span, yLine)
      ctx.stroke()

      // moving parts
      part = (part + 0.8) % 46
      ctx.fillStyle = '#3ea6ff'
      for (let x = pad - 20; x < pad + span; x += 46) {
        const px = x + part
        if (px >= pad - 6 && px <= pad + span + 6) {
          ctx.beginPath()
          ctx.arc(px, yLine, 4, 0, Math.PI * 2)
          ctx.fill()
        }
      }

      // stations
      stations.forEach((s, i) => {
        const x = pad + (n === 1 ? span / 2 : i * step)
        const live = s.line_id ? lineLive[s.line_id] : undefined
        const alarm = Number(live?.alarm ?? 0)
        const isBottleneck = s.status === 'BOTTLENECK' || s.id === template.bottleneck_node_id
        const base = statusColor(s.status)
        const fill = alarm !== 0 ? '#ef5350' : isBottleneck ? '#4a1f26' : '#1a2532'
        const stroke = alarm !== 0 ? '#ef5350' : base
        const bw = Math.min(96, Math.max(58, span / n - 10))
        const bh = 54
        const by = yLine - bh - 26

        ctx.fillStyle = fill
        ctx.strokeStyle = stroke
        ctx.lineWidth = isBottleneck ? 2 : 1
        ctx.beginPath()
        ctx.rect(x - bw / 2, by, bw, bh)
        ctx.fill()
        ctx.stroke()

        // connector
        ctx.strokeStyle = stroke
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.moveTo(x, by + bh)
        ctx.lineTo(x, yLine - 7)
        ctx.stroke()

        ctx.fillStyle = '#e6edf5'
        ctx.font = '11px Inter, system-ui, sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(s.id, x, by + 18)
        ctx.fillStyle = '#8a9bb0'
        ctx.font = '10px Inter, system-ui, sans-serif'
        const short = s.name.length > 14 ? `${s.name.slice(0, 13)}…` : s.name
        ctx.fillText(short, x, by + 34)

        if (isBottleneck) {
          ctx.fillStyle = '#f2b544'
          ctx.font = 'bold 9px JetBrains Mono, monospace'
          ctx.fillText('BOTTLENECK', x, by - 6)
        }
        if (s.line_id) {
          ctx.fillStyle = '#5c6b7d'
          ctx.font = '9px JetBrains Mono, monospace'
          ctx.fillText(s.line_id, x, yLine + 22)
        }
      })

      // legend / derived queue proxy
      const bLine = template.bottleneck_line_id
      const bLive = bLine ? lineLive[bLine] : undefined
      const load = bLive?.load
      ctx.textAlign = 'left'
      ctx.fillStyle = '#8a9bb0'
      ctx.font = '11px Inter, system-ui, sans-serif'
      const proxy =
        typeof load === 'number'
          ? `нагрузка ${bLine}: ${Math.round(load)}% (сигнал OPC UA)`
          : `узел ${template.bottleneck_node_id}: расчётный показатель витрины`
      ctx.fillText(proxy, 12, h - 12)

      raf = requestAnimationFrame(render)
    }

    raf = requestAnimationFrame(render)
    return () => cancelAnimationFrame(raf)
  }, [template, lineLive])

  return (
    <div ref={wrapRef} style={{ width: '100%', overflow: 'hidden' }}>
      <canvas
        ref={canvasRef}
        role="img"
        aria-label={`Схема потока: ${template.name}`}
        style={{ display: 'block', maxWidth: '100%', borderRadius: 8, border: '1px solid var(--border)' }}
      />
    </div>
  )
}