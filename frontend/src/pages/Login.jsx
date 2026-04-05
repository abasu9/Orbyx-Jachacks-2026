import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Login.css'

const DEMO_EMAIL = 'emphr@company.in'
const DEMO_PASS = 'admin'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function handleLogin(e) {
    e?.preventDefault()
    setError('')

    if (email !== DEMO_EMAIL || password !== DEMO_PASS) {
      setError('Invalid email or password')
      return
    }

    setLoading(true)
    setTimeout(() => {
      sessionStorage.setItem('cull_auth', '1')
      navigate('/dashboard')
    }, 400)
  }

  function handleDemoLogin() {
    setEmail(DEMO_EMAIL)
    setPassword(DEMO_PASS)
    setError('')
    setLoading(true)
    setTimeout(() => {
      sessionStorage.setItem('cull_auth', '1')
      navigate('/dashboard')
    }, 600)
  }

  return (
    <div className="login-page">
      {/* Ambient glow */}
      <div className="login-glow" />

      <div className="login-card">
        {/* Logo / Brand */}
        <div className="login-brand">
          <img src="/cull-log.jpeg" alt="CULL" className="login-logo-img" />
          <h1 className="login-title">CULL</h1>
          <p className="login-subtitle">Employee Performance AI</p>
        </div>

        {/* Form */}
        <form className="login-form" onSubmit={handleLogin}>
          <div className="input-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>

          <div className="input-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          {error && <p className="login-error">{error}</p>}

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? 'Signing in…' : 'Sign In'}
          </button>

          <div className="login-divider">
            <span>or</span>
          </div>

          <button
            type="button"
            className="btn-demo"
            onClick={handleDemoLogin}
            disabled={loading}
          >
            ⚡ Demo Login
          </button>
        </form>

        <p className="login-footer">
          Powered by <span className="accent">CULL</span> AI Engine
        </p>
      </div>
    </div>
  )
}
