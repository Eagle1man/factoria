import type { ReactNode } from 'react'
import type { Quality } from '../lib/api'

export function Panel({
  title,
  hint,
  actions,
  children,
}: {
  title?: string
  hint?: string
  actions?: ReactNode
  children: ReactNode
}) {
  return (
    <section className="panel">
      {(title || actions) && (
        <header className="panel-head">
          <div>
            {title && <div className="panel-title">{title}</div>}
            {hint && <div className="panel-hint">{hint}</div>}
          </div>
          {actions}
        </header>
      )}
      {children}
    </section>
  )
}

export function Kpi({
  label,
  value,
  unit,
  tone,
}: {
  label: string
  value: string | number
  unit?: string
  tone?: 'good' | 'warn' | 'bad'
}) {
  const color = tone === 'bad' ? 'var(--danger)' : tone === 'warn' ? 'var(--warning)' : undefined
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value" style={color ? { color } : undefined}>
        {value}
        {unit && <span className="kpi-unit">{unit}</span>}
      </div>
    </div>
  )
}

export function Badge({
  tone = 'info',
  children,
}: {
  tone?: 'good' | 'warn' | 'bad' | 'info'
  children: ReactNode
}) {
  const className =
    tone === 'good' ? 'badge badge-good' : tone === 'warn' ? 'badge badge-warn' : tone === 'bad' ? 'badge badge-bad' : 'badge badge-info'
  return <span className={className}>{children}</span>
}

const QUALITY_LABEL: Record<Quality, string> = {
  GOOD: 'норма',
  STALE: 'устарело',
  BAD: 'нет данных',
}

export function QualityBadge({ quality }: { quality: Quality }) {
  const tone = quality === 'GOOD' ? 'good' : quality === 'STALE' ? 'warn' : 'bad'
  return <Badge tone={tone}>{QUALITY_LABEL[quality]}</Badge>
}

export function EmptyState({
  title,
  hint,
  icon,
}: {
  title: string
  hint?: string
  icon?: ReactNode
}) {
  return (
    <div className="empty">
      {icon}
      <div style={{ color: 'var(--ink)', fontSize: 14 }}>{title}</div>
      {hint && <div style={{ fontSize: 12 }}>{hint}</div>}
    </div>
  )
}

export function ErrorState({
  message,
  code,
  onRetry,
}: {
  message: string
  code?: string | number
  onRetry?: () => void
}) {
  return (
    <div className="error">
      <div className="error-title">Не удалось загрузить</div>
      <div className="mono">{code ? `${code}: ` : ''}{message}</div>
      {onRetry && (
        <button className="btn btn-secondary" onClick={onRetry}>
          Повторить
        </button>
      )}
    </div>
  )
}

export function SkeletonRows({ rows = 4 }: { rows?: number }) {
  return (
    <div style={{ display: 'grid', gap: 10 }} aria-hidden>
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="skeleton" style={{ width: `${92 - index * 7}%` }} />
      ))}
    </div>
  )
}

export function formatNumber(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined) return '—'
  return value.toLocaleString('ru-RU', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const date = new Date(iso)
  return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}
