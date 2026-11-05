import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  Box,
  Boxes,
  Bot,
  Factory,
  FileText,
  FlaskConical,
  LayoutDashboard,
  ScrollText,
  Settings as SettingsIcon,
  ShieldCheck,
} from 'lucide-react'
import { api, type Health } from '../lib/api'
import { useAuth } from '../lib/auth'

const NAV = [
  { to: '/', label: 'Обзор', icon: LayoutDashboard, end: true },
  { to: '/documents', label: 'Документы 1С', icon: FileText },
  { to: '/production', label: 'Производство', icon: Factory },
  { to: '/twin', label: 'Двойник', icon: Boxes },
  { to: '/experiments', label: 'Эксперименты', icon: FlaskConical },
  { to: '/agents', label: 'Агенты', icon: Bot },
  { to: '/approvals', label: 'Согласования', icon: ShieldCheck },
  { to: '/audit', label: 'Журнал', icon: ScrollText },
  { to: '/settings', label: 'Настройки', icon: SettingsIcon },
  { to: '/scene', label: '3D-сцена', icon: Box },
]

const TITLES: Record<string, string> = {
  '/': 'Обзор',
  '/documents': 'Документы 1С',
  '/production': 'Производство',
  '/twin': 'Цифровой двойник',
  '/experiments': 'Эксперименты',
  '/agents': 'Агенты и трассы',
  '/approvals': 'Согласования',
  '/audit': 'Журнал',
  '/settings': 'Настройки',
  '/scene': '3D-сцена',
}

function StatusChip({ tone, label }: { tone: string; label: string }) {
  const className = tone === 'good' ? 'dot good' : tone === 'warn' ? 'dot warn' : tone === 'bad' ? 'dot bad' : 'dot'
  return (
    <span className="chip">
      <span className={className} />
      {label}
    </span>
  )
}

export default function Layout() {
  const location = useLocation()
  const { role, logout } = useAuth()
  const [health, setHealth] = useState<Health | null>(null)
  const [clock, setClock] = useState(() => new Date())

  useEffect(() => {
    let alive = true
    const load = () => {
      api
        .health()
        .then((value) => alive && setHealth(value))
        .catch(() => alive && setHealth(null))
    }
    load()
    const timer = window.setInterval(load, 10_000)
    return () => {
      alive = false
      window.clearInterval(timer)
    }
  }, [])

  useEffect(() => {
    const timer = window.setInterval(() => setClock(new Date()), 30_000)
    return () => window.clearInterval(timer)
  }, [])

  const opcua = health?.sources.opcua.state ?? 'down'
  const opcuaTone = opcua === 'connected' ? 'good' : opcua === 'unknown' ? 'warn' : 'bad'
  const notGood = health?.tags.not_good ?? 0

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-name">FACTORIA &amp; AI</span>
          <span className="brand-version">v0.3</span>
        </div>
        <nav style={{ display: 'grid', gap: 2 }}>
          {NAV.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                title={item.label}
              >
                <Icon className="nav-icon" size={16} strokeWidth={1.6} aria-hidden />
                <span className="nav-label">{item.label}</span>
              </NavLink>
            )
          })}
        </nav>
      </aside>

      <div className="main">
        <header className="topbar">
          <span className="topbar-title">{TITLES[location.pathname] ?? 'FACTORIA & AI'}</span>
          <StatusChip tone={opcuaTone} label={`OPC UA: ${opcua === 'connected' ? 'связь' : opcua === 'unknown' ? 'ожидание' : 'нет связи'}`} />
          <StatusChip tone={notGood === 0 ? 'good' : 'warn'} label={`теги: ${notGood === 0 ? 'все в норме' : `${notGood} не в норме`}`} />
          <span className="chip optional">{health?.env ?? '—'}</span>
          <span className="chip mono">
            {clock.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
          </span>
          <span className="chip">{role ?? '—'}</span>
          <button className="btn btn-secondary" onClick={logout}>
            Выйти
          </button>
        </header>

        <div className="banner">Режим чтения · запись в 1С отключена</div>

        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
