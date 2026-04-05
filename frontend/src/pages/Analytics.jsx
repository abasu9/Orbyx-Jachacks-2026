import { useNavigate } from 'react-router-dom'
import { useEffect, useState, useMemo } from 'react'
import { Chart as ChartJS, LinearScale, PointElement, Tooltip, Legend } from 'chart.js'
import { Scatter } from 'react-chartjs-2'
import './Analytics.css'

ChartJS.register(LinearScale, PointElement, Tooltip, Legend)

const PAGE_SIZE = 10

const COLUMNS = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'level', label: 'Level', sortable: true },
  { key: 'apr', label: 'APR (latest)', sortable: true },
  { key: 'pip', label: 'PIP', sortable: true },
  { key: 'ranking', label: 'Ranking', sortable: true },
  { key: 'roi', label: 'ROI', sortable: true },
  { key: 'gh_username', label: 'GitHub', sortable: false },
  { key: 'joiningdate', label: 'Joined', sortable: true },
]

function latestApr(apr) {
  if (apr == null) return null
  // apr can be an array [1.06, 0.14, 0.22] or a dict {"2024": 1.06}
  if (Array.isArray(apr)) {
    if (apr.length === 0) return null
    return parseFloat(apr[apr.length - 1])
  }
  if (typeof apr === 'object') {
    const keys = Object.keys(apr).sort()
    if (keys.length === 0) return null
    return parseFloat(apr[keys[keys.length - 1]])
  }
  return null
}

export default function Analytics() {
  const navigate = useNavigate()
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('name')
  const [sortDir, setSortDir] = useState('asc')
  const [page, setPage] = useState(1)

  useEffect(() => {
    if (!sessionStorage.getItem('cull_auth')) {
      navigate('/login', { replace: true })
      return
    }
    fetchEmployees()
  }, [navigate])

  async function fetchEmployees() {
    setLoading(true)
    setError('')
    try {
      const resp = await fetch('/api/employees')
      if (!resp.ok) throw new Error(`Error ${resp.status}`)
      const data = await resp.json()
      setEmployees(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Derived: filter → sort → paginate
  const filtered = useMemo(() => {
    if (!search.trim()) return employees
    const q = search.toLowerCase()
    return employees.filter(e =>
      (e.name || '').toLowerCase().includes(q) ||
      (e.level || '').toLowerCase().includes(q) ||
      (e.gh_username || '').toLowerCase().includes(q)
    )
  }, [employees, search])

  const sorted = useMemo(() => {
    const arr = [...filtered]
    arr.sort((a, b) => {
      let va, vb
      if (sortKey === 'apr') {
        va = latestApr(a.apr) ?? -1
        vb = latestApr(b.apr) ?? -1
      } else {
        va = a[sortKey] ?? ''
        vb = b[sortKey] ?? ''
      }
      if (typeof va === 'string') va = va.toLowerCase()
      if (typeof vb === 'string') vb = vb.toLowerCase()
      if (va < vb) return sortDir === 'asc' ? -1 : 1
      if (va > vb) return sortDir === 'asc' ? 1 : -1
      return 0
    })
    return arr
  }, [filtered, sortKey, sortDir])

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE))
  const paged = sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  function handleSort(key) {
    if (!COLUMNS.find(c => c.key === key)?.sortable) return
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
    setPage(1)
  }

  function handleLogout() {
    sessionStorage.removeItem('cull_auth')
    navigate('/login')
  }

  // ── Heatmap: Ranking (x) vs ROI (y) ──────────────────────
  const heatmapData = useMemo(() => {
    const points = employees
      .filter(e => e.ranking != null && e.roi != null && (e.ranking > 0 || e.roi > 0))
      .map(e => ({
        x: e.ranking,
        y: e.roi,
        name: e.name,
        level: e.level,
      }))

    return {
      datasets: [
        {
          label: 'High',
          data: points.filter(p => (p.x + p.y) / 2 >= 0.6),
          backgroundColor: 'rgba(34,197,94,0.85)',
          pointRadius: 7,
          pointHoverRadius: 10,
        },
        {
          label: 'Moderate',
          data: points.filter(p => { const s = (p.x + p.y) / 2; return s >= 0.35 && s < 0.6 }),
          backgroundColor: 'rgba(250,204,21,0.85)',
          pointRadius: 7,
          pointHoverRadius: 10,
        },
        {
          label: 'Low',
          data: points.filter(p => (p.x + p.y) / 2 < 0.35),
          backgroundColor: 'rgba(239,68,68,0.85)',
          pointRadius: 7,
          pointHoverRadius: 10,
        },
      ],
    }
  }, [employees])

  const heatmapOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#a1a1aa', font: { size: 12 }, usePointStyle: true, pointStyle: 'circle', padding: 16 },
      },
      tooltip: {
        backgroundColor: '#1a1a1a',
        borderColor: '#333',
        borderWidth: 1,
        titleColor: '#fafafa',
        bodyColor: '#a1a1aa',
        padding: 10,
        callbacks: {
          label(ctx) {
            const p = ctx.raw
            return `${p.name} (${p.level}) — Ranking: ${p.x.toFixed(4)}, ROI: ${p.y.toFixed(4)}`
          },
        },
      },
    },
    scales: {
      x: {
        title: { display: true, text: 'Ranking', color: '#a1a1aa', font: { size: 13 } },
        min: 0, max: 1,
        grid: { color: 'rgba(255,255,255,0.05)' },
        ticks: { color: '#71717a', stepSize: 0.2 },
      },
      y: {
        title: { display: true, text: 'ROI', color: '#a1a1aa', font: { size: 13 } },
        min: 0,
        grid: { color: 'rgba(255,255,255,0.05)' },
        ticks: { color: '#71717a' },
      },
    },
  }), [])

  return (
    <div className="analytics-page">
      <header className="dash-header">
        <div className="dash-brand">
          <img src="/cull-log.jpeg" alt="CULL" className="dash-logo-img" />
          <div>
            <span className="dash-logo-text">CULL</span>
            <span className="dash-tag">Analytics</span>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-nav" onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button className="btn-logout" onClick={handleLogout}>Sign Out</button>
        </div>
      </header>

      <main className="an-main">
        <div className="an-toolbar">
          <input
            className="an-search"
            type="text"
            placeholder="Search by name, level, or GitHub..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
          />
          <button className="btn-refresh" onClick={fetchEmployees} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {error && <div className="an-error">{error}</div>}

        {/* Heatmap: Ranking vs ROI */}
        {!loading && heatmapData.datasets.some(d => d.data.length > 0) && (
          <div className="heatmap-card">
            <h3 className="heatmap-title">Employee Heatmap — Ranking vs ROI</h3>
            <div className="heatmap-chart-wrap">
              <Scatter data={heatmapData} options={heatmapOptions} />
            </div>
          </div>
        )}

        <div className="an-table-wrap">
          <table className="an-table">
            <thead>
              <tr>
                {COLUMNS.map(col => (
                  <th
                    key={col.key}
                    className={col.sortable ? 'sortable' : ''}
                    onClick={() => handleSort(col.key)}
                  >
                    {col.label}
                    {sortKey === col.key && (
                      <span className="sort-arrow">{sortDir === 'asc' ? ' ▲' : ' ▼'}</span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={COLUMNS.length} className="an-loading">Loading employees...</td></tr>
              ) : paged.length === 0 ? (
                <tr><td colSpan={COLUMNS.length} className="an-empty">No employees found.</td></tr>
              ) : paged.map(emp => (
                <tr key={emp.id}>
                  <td className="td-name">{emp.name}</td>
                  <td>{emp.level || '—'}</td>
                  <td>{latestApr(emp.apr) != null ? latestApr(emp.apr).toFixed(2) : '—'}</td>
                  <td>{emp.pip ?? '—'}</td>
                  <td>{emp.ranking != null ? emp.ranking.toFixed(4) : '—'}</td>
                  <td>{emp.roi != null ? emp.roi.toFixed(4) : '—'}</td>
                  <td className="td-gh">{emp.gh_username || '—'}</td>
                  <td>{emp.joiningdate || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && sorted.length > PAGE_SIZE && (
          <div className="an-pagination">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Prev</button>
            <span className="page-info">Page {page} of {totalPages} ({sorted.length} records)</span>
            <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next</button>
          </div>
        )}
      </main>
    </div>
  )
}
