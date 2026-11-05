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
import Stub from './pages/Stub'

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
          <Route
            path="twin"
            element={
              <Stub
                title="Цифровой двойник"
                subtitle="Версия модели, точность, покрытие"
                stage="этапе 2 модели данных"
                items={[
                  'Статус EXPERIMENTAL и дата сборки',
                  'Метрики точности и покрытия по линиям',
                  'Сущности и связи семантической модели',
                  'Предупреждения о расхождении с фактом',
                ]}
              />
            }
          />
          <Route
            path="experiments"
            element={
              <Stub
                title="Эксперименты"
                subtitle="Запуски симуляции и сравнение результатов"
                stage="этапе 8"
                items={[
                  'Форма запуска: сценарий, seed, горизонт',
                  'История запусков с воспроизводимым seed',
                  'Сравнение двух прогонов по метрикам',
                  'Пометка «данные симуляции, не факт»',
                ]}
              />
            }
          />
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
              <Stub
                title="3D-сцена"
                subtitle="Модель линии и привязка к тегам"
                stage="этапе 3, после панели"
                items={[
                  'Три линии с вращением ротора по Speed.PV',
                  'Нагрев корпуса по Temp.PV',
                  'Индикатор работы и мигание при аварии',
                  'Серый меш при качестве STALE/BAD',
                ]}
              />
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
