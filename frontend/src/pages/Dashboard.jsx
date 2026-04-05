import { useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import './Dashboard.css'

const METRICS = [
  { key: 'apr', label: 'APR', desc: 'Annual Performance Rating', default: true },
  { key: 'pip', label: 'PIP', desc: 'Performance Improvement Program', default: true },
]

const PHASES = [
  'Fetching employee records...',
  'Computing performance rankings...',
  'Collecting GitHub data & AI scoring...',
  'Writing results to database...',
  'Finalizing reports...',
]

export default function Dashboard() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState(
    () => new Set(METRICS.filter(m => m.default).map(m => m.key))
  )
  const [status, setStatus] = useState('idle')
  const [phase, setPhase] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!sessionStorage.getItem('cull_auth')) {
      navigate('/login', { replace: true })
    }
  }, [navigate])

  useEffect(() => {
    if (status !== 'running') return
    const interval = setInterval(() => {
      setPhase(p => (p + 1) % PHASES.length)
    }, 6000)
    return () => clearInterval(interval)
  }, [status])

  function toggleMetric(key) {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  async function startAnalytics() {
    setStatus('running')
    setPhase(0)
    setError('')

    try {
      const resp = await fetch('/api/handle', { method: 'POST' })
      if (!resp.ok) {
        const body = await resp.text()
        throw new Error(body || `Server error ${resp.status}`)
      }
      await resp.json()
      setStatus('done')
      navigate('/analytics')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  function handleLogout() {
    sessionStorage.removeItem('cull_auth')
    navigate('/login')
  }

  return (
    <div className="dashboard-page">
      <header className="dash-header">
        <div className="dash-brand">
          <img src="/cull-log.jpeg" alt="CULL" className="dash-logo-img" />
          <div>
            <span className="dash-logo-text">CULL</span>
            <span className="dash-tag">Dashboard</span>
          </div>
        </div>
        <button className="btn-logout" onClick={handleLogout}>Sign Out</button>
      </header>

      <main className="dash-main">
        <div className="analytics-card">
          <div className="ac-header">
            <h2>Employee Performance Metrics</h2>
            <p className="ac-sub">
              Select the data points to include in the analysis.
              Our AI agents will collect data, compute rankings,
              evaluate GitHub contributions, and generate reports.
            </p>
          </div>

          <div className="ac-metrics">
            {METRICS.map(m => (
              <button
                key={m.key}
                className={`metric-pill ${selected.has(m.key) ? 'active' : ''}`}
                onClick={() => toggleMetric(m.key)}
                disabled={status === 'running'}
              >
                <span className="pill-check">{selected.has(m.key) ? '\u2713' : ''}</span>
                <div className="pill-text">
                  <span className="pill-label">{m.label}</span>
                  <span className="pill-desc">{m.desc}</span>
                </div>
              </button>
            ))}
          </div>

          <div className="ac-highlights">
            <div className="highlight"><span className="hl-icon">&#129302;</span><span>AI-powered GitHub analysis</span></div>
            <div className="highlight"><span className="hl-icon">&#128202;</span><span>Normalized 0-1 ranking scores</span></div>
            <div className="highlight"><span className="hl-icon">&#128176;</span><span>ROI per employee with tenure factor</span></div>
            <div className="highlight"><span className="hl-icon">&#9889;</span><span>Automated data collection pipeline</span></div>
          </div>

          <div className="ac-action">
            {status === 'idle' && (
              <button className="btn-start" onClick={startAnalytics} disabled={selected.size === 0}>
                Start Analytics
              </button>
            )}

            {status === 'running' && (
              <div className="ac-running">
                <div className="spinner" />
                <div className="run-text">
                  <p className="run-phase">{PHASES[phase]}</p>
                  <p className="run-hint">This may take a few minutes depending on the number of employees.</p>
                </div>
              </div>
            )}

            {status === 'error' && (
              <div className="ac-result">
                <div className="result-banner error">
                  <span>&#10060;</span>
                  <span>Pipeline failed: {error}</span>
                </div>
                <button className="btn-start small" onClick={() => setStatus('idle')}>
                  Try Again
                </button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
