import { useEffect, useRef, useState } from 'react'
import type { Quality, TagValue } from './api'

export type StreamState = 'connecting' | 'open' | 'closed'

export interface CommandEvent {
  type: 'command_status'
  command_id: string
  status: string
  autonomy_level?: string
  line_id?: string
}

interface Delta {
  seq: number
  values: Record<string, TagValue>
}

const BACKOFF = [1000, 2000, 5000, 10000]

/** Живые значения тегов по WS: snapshot → delta, переподключение с resume. */
export function useTags(token: string | null): {
  values: Record<string, TagValue>
  seq: number
  state: StreamState
  commandEvent: CommandEvent | null
} {
  const [values, setValues] = useState<Record<string, TagValue>>({})
  const [seq, setSeq] = useState(0)
  const [state, setState] = useState<StreamState>('connecting')
  const [commandEvent, setCommandEvent] = useState<CommandEvent | null>(null)
  const seqRef = useRef(0)

  useEffect(() => {
    if (!token) return
    let socket: WebSocket | null = null
    let reconnectTimer: number | undefined
    let attempts = 0
    let closed = false

    const connect = () => {
      if (closed) return
      const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
      socket = new WebSocket(`${protocol}://${location.host}/ws?token=${encodeURIComponent(token)}`)
      setState('connecting')

      socket.onopen = () => {
        attempts = 0
        setState('open')
        socket?.send(
          JSON.stringify({
            type: 'subscribe',
            tags: [],
            delta_only: true,
            min_interval_ms: 100,
          }),
        )
        if (seqRef.current > 0) socket?.send(JSON.stringify({ type: 'resume', last_seq: seqRef.current }))
      }

      socket.onmessage = (event) => {
        const message = JSON.parse(event.data) as { type: string } & Partial<Delta>
        if (message.type === 'snapshot' || message.type === 'delta') {
          if (message.values) {
            setValues((previous) =>
              message.type === 'snapshot' ? { ...message.values } : { ...previous, ...message.values },
            )
          }
          if (typeof message.seq === 'number') {
            seqRef.current = message.seq
            setSeq(message.seq)
          }
        } else if (message.type === 'command_status') {
          setCommandEvent(message as CommandEvent)
        }
      }

      socket.onclose = () => {
        setState('closed')
        if (closed) return
        const delay = BACKOFF[Math.min(attempts, BACKOFF.length - 1)]
        attempts += 1
        reconnectTimer = window.setTimeout(connect, delay)
      }

      socket.onerror = () => socket?.close()
    }

    connect()
    return () => {
      closed = true
      window.clearTimeout(reconnectTimer)
      socket?.close()
    }
  }, [token])

  return { values, seq, state, commandEvent }
}

export function qualityOf(value: TagValue | undefined): Quality {
  return value?.q ?? 'BAD'
}
