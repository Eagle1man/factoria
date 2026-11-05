import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [username, setUsername] = useState('operator')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(username, password)
      navigate('/', { replace: true })
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : 'вход не выполнен')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login">
      <form className="login-card" onSubmit={submit}>
        <div>
          <div className="login-title">FACTORIA &amp; AI</div>
          <div className="login-note">Пульт диспетчера производственного контура</div>
        </div>

        <div className="field">
          <label htmlFor="username">Пользователь</label>
          <input
            id="username"
            className="input"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
          />
        </div>

        <div className="field">
          <label htmlFor="password">Пароль</label>
          <input
            id="password"
            className="input"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
          />
        </div>

        {error && <div className="form-error">{error}</div>}

        <button className="btn btn-primary" type="submit" disabled={busy || !password}>
          {busy ? 'Проверка…' : 'Войти'}
        </button>

        <div className="login-note">
          Учётную запись выдаёт администратор контура. В dev-среде доступны
          пользователи <span className="mono">operator</span>,{' '}
          <span className="mono">technologist</span>, <span className="mono">auditor</span>,{' '}
          <span className="mono">lead</span>.
        </div>
      </form>
    </div>
  )
}
