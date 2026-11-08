import React from 'react'
import ReactDOM from 'react-dom/client'
import { MemoryRouter } from 'react-router-dom'
import '@fontsource-variable/inter'
import '@fontsource-variable/jetbrains-mono'
import '../styles.css'
import App from '../App'
import './mock'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MemoryRouter initialEntries={['/flow']}>
      <App />
    </MemoryRouter>
  </React.StrictMode>,
)
