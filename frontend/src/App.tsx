import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { AuraProvider } from './context/AuraContext'
import Dashboard from './pages/Dashboard'

import TranslationBridge from './pages/TranslationBridge'
import EmergencySettings from './pages/EmergencySettings'
import Login from './pages/Login'
import './index.css'

function Navbar() {
  const { user, logout } = useAuth()

  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-brand" style={{ textDecoration: 'none' }}>
        <div className="navbar-logo">✦</div>
        <span className="navbar-title">AURA</span>
      </NavLink>

      <div className="navbar-links">
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Active Session</NavLink>

        <NavLink to="/translate" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Translation</NavLink>
        <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Settings</NavLink>
      </div>

      <div className="navbar-right">
        <div className="status-badge">
          <div className="status-dot"></div>
          SYSTEM ONLINE
        </div>
        {user && (
          <>
            <span style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user.name || user.email}
            </span>
            <button className="icon-btn" onClick={logout} title="Sign out">⏻</button>
          </>
        )}
      </div>
    </nav>
  )
}

function ProtectedRoutes() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'var(--bg-primary)' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: 56, height: 56, borderRadius: 16, background: 'var(--primary)', display: 'inline-grid', placeItems: 'center', fontSize: 28, animation: 'orb-pulse 1.5s infinite' }}>✦</div>
          <p style={{ marginTop: 16, color: 'var(--text-secondary)' }}>Loading AURA...</p>
        </div>
      </div>
    )
  }

  if (!user) return <Login />

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Dashboard />} />

        <Route path="/translate" element={<TranslationBridge />} />
        <Route path="/settings" element={<EmergencySettings />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AuraProvider>
          <ProtectedRoutes />
        </AuraProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
