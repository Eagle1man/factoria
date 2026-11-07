import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/auth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Overview from './pages/Overview'
import Production from './pages/Production'
import Audit from './pages/Audit'
import Settings from './pages/Settings'
import Approvals from './pages/Approvals'
import Documents from './pages/Documents'
import Experiments from './pages/Experiments'
import TwinPage from './pages/Twin'
import Stub from './pages/Stub'

const Scene = lazy(() => import('./pages/Scene'))

function Protected({ children }: { children: React.ReactNode }) {
  const { ready, role } = useAuth()
  if (!ready) return <div className="login"><div className="skeleton" style={{ width: 200 }} /></div>
  if (!role) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <Protected>
              <Layout />
            </Protected>
          }
        >
          <Route index element={<Overview />} />
          <Route path="production" element={<Production />} />
          <Route path="documents" element={<Documents />} />
          <Route path="twin" element={<TwinPage />} />
          <Route path="experiments" element={<Experiments />} />
          <Route
            path="agents"
            element={
              <Stub
                title="Агенты и трассы"
                subtitle="Сессии, шаги, расход токенов"
                stage="этапе 5"
                items={[
                  'Карточки агентов и их роли',
                  'Очередь задач и текущий шаг',
                  'Таймлайн трассы с tool-call и evidence',
                  'Бюджеты токенов и признак budget_exhausted',
                ]}
              />
            }
          />
          <Route path="approvals" element={<Approvals />} />
          <Route
            path="scene"
            element={
              <Suspense fallback={<div className="skeleton" style={{ height: 480 }} />}>
                <Scene />
              </Suspense>
            }
          />
          <Route path="audit" element={<Audit />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
