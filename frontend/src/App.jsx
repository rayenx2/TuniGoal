import { useState, useEffect, useCallback } from 'react'

// ── Styles ────────────────────────────────────────────────────────────────────
const s = {
  wrap:   { minHeight: '100vh', background: '#0a0f1a', color: '#f1f5f9', fontFamily: 'system-ui, sans-serif' },
  header: { background: 'rgba(10,15,26,0.95)', borderBottom: '1px solid #1e293b', padding: '0 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 56, position: 'sticky', top: 0, zIndex: 100, backdropFilter: 'blur(12px)' },
  logo:   { width: 32, height: 32, background: 'linear-gradient(135deg,#10b981,#06b6d4)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 16, color: '#0a0f1a', marginRight: 12 },
  hero:   { textAlign: 'center', padding: '48px 32px 32px', borderBottom: '1px solid #1e293b' },
  heroTitle: { fontSize: 42, fontWeight: 800, margin: 0, lineHeight: 1.1 },
  accent: { color: '#10b981' },
  heroSub: { fontSize: 15, color: '#64748b', margin: '12px 0 20px', maxWidth: 560, marginLeft: 'auto', marginRight: 'auto' },
  badge:  { display: 'inline-flex', alignItems: 'center', gap: 6, background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: 20, padding: '4px 12px', fontSize: 12, color: '#10b981' },
  content: { maxWidth: 1200, margin: '0 auto', padding: '32px 24px' },
  tabs:   { display: 'flex', gap: 0, borderBottom: '1px solid #1e293b', marginBottom: 32 },
  tab:    (a) => ({ padding: '12px 20px', background: 'none', border: 'none', color: a ? '#10b981' : '#64748b', fontWeight: 600, fontSize: 14, cursor: 'pointer', borderBottom: a ? '2px solid #10b981' : '2px solid transparent', transition: 'all 0.2s' }),
  card:   { background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)', borderRadius: 12, padding: 24 },
  grid2:  { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  grid4:  { display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 24 },
  kpi:    { background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.4)', borderRadius: 12, padding: '20px 24px' },
  kpiVal: { fontSize: 32, fontWeight: 800, lineHeight: 1.1, marginBottom: 2 },
  kpiLbl: { fontSize: 12, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1 },
  kpiSub: { fontSize: 11, color: '#475569', marginTop: 4 },
  sectionTitle: { fontSize: 16, fontWeight: 700, color: '#f1f5f9', marginBottom: 0 },
  table:  { width: '100%', borderCollapse: 'collapse', fontSize: 14 },
  th:     { padding: '10px 12px', textAlign: 'left', color: '#475569', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5, borderBottom: '1px solid #1e293b' },
  td:     { padding: '10px 12px', borderBottom: '1px solid rgba(30,41,59,0.5)', color: '#94a3b8' },
  select: { background: '#0f172a', border: '1px solid rgba(51,65,85,0.6)', borderRadius: 8, color: '#f1f5f9', padding: '10px 14px', fontSize: 14, width: '100%', cursor: 'pointer', outline: 'none' },
  btn:    (variant) => ({
    padding: '11px 24px', borderRadius: 8, border: 'none', fontWeight: 600, fontSize: 14,
    cursor: 'pointer', transition: 'all 0.2s',
    background: variant === 'primary' ? 'linear-gradient(135deg,#10b981,#06b6d4)' : 'rgba(51,65,85,0.5)',
    color: variant === 'primary' ? '#0a0f1a' : '#f1f5f9',
  }),
  tag:    (color) => ({ display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
    background: color === 'green' ? 'rgba(16,185,129,0.15)' : color === 'yellow' ? 'rgba(234,179,8,0.15)' : 'rgba(239,68,68,0.15)',
    color:      color === 'green' ? '#10b981'               : color === 'yellow' ? '#eab308'              : '#ef4444' }),
  dot:    (color) => ({ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', marginRight: 6,
    background: color === 'green' ? '#10b981' : color === 'yellow' ? '#eab308' : '#ef4444' }),
}

// ── API helper ────────────────────────────────────────────────────────────────
async function api(path, opts) {
  try {
    const r = await fetch(`/api${path}`, opts)
    if (!r.ok) return null
    return await r.json()
  } catch { return null }
}

// ── Dashboard Tab ─────────────────────────────────────────────────────────────
function DashboardTab() {
  const [matches,   setMatches]   = useState([])
  const [warehouse, setWarehouse] = useState(null)
  const [pipStatus, setPipStatus] = useState(null)
  const [triggering, setTriggering] = useState(false)
  const [trigMsg, setTrigMsg] = useState(null)

  const load = useCallback(async () => {
    const [m, w, p] = await Promise.all([
      api('/matches'), api('/warehouse/summary'), api('/pipeline/status')
    ])
    if (m) setMatches(m)
    if (w) setWarehouse(w)
    if (p) setPipStatus(p)
  }, [])

  useEffect(() => { load() }, [load])

  const triggerPipeline = async () => {
    setTriggering(true); setTrigMsg(null)
    const r = await api('/pipeline/trigger', { method: 'POST' })
    setTriggering(false)
    if (r?.triggered) {
      setTrigMsg({ ok: true, text: `DAG triggered — run ID: ${r.run_id}` })
      setTimeout(load, 3000)
    } else {
      setTrigMsg({ ok: false, text: r?.detail?.detail || 'Airflow unreachable. Start it with: docker compose up -d' })
    }
  }

  const stateColor = (s) => s === 'success' ? 'green' : s === 'running' ? 'yellow' : s === 'failed' ? 'red' : 'yellow'

  return (
    <div style={{ display: 'grid', gap: 24 }}>

      {/* KPI row */}
      <div style={s.grid4}>
        {[
          { val: warehouse?.raw_matches  ?? '…', lbl: 'Fixtures Ingested', sub: 'raw_matches staging' },
          { val: warehouse?.raw_standings ?? '…', lbl: 'Teams in Standings', sub: 'raw_standings' },
          { val: warehouse?.fact_matches  ?? 0,  lbl: 'Gold Facts',         sub: 'fact_matches (post-Spark)' },
          { val: warehouse?.dim_teams     ?? 0,  lbl: 'Team Dimensions',    sub: 'dim_teams (post-Spark)' },
        ].map(k => (
          <div key={k.lbl} style={s.kpi}>
            <div style={{ ...s.kpiVal, color: '#10b981' }}>{k.val}</div>
            <div style={s.kpiLbl}>{k.lbl}</div>
            <div style={s.kpiSub}>{k.sub}</div>
          </div>
        ))}
      </div>

      {/* Pipeline control */}
      <div style={s.card}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <div style={s.sectionTitle}><span style={s.accent}>//</span> Pipeline Control — Airflow DAG</div>
          <a href="http://localhost:8080" target="_blank" rel="noreferrer"
             style={{ fontSize: 12, color: '#64748b', textDecoration: 'none' }}>
            Open Airflow UI →
          </a>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          {/* Status */}
          <div style={{ background: '#0f172a', borderRadius: 10, padding: 20 }}>
            <div style={{ fontSize: 12, color: '#64748b', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>Last Run</div>
            {pipStatus?.last_run === null && <div style={{ color: '#64748b' }}>No runs yet — trigger below</div>}
            {pipStatus?.state && (
              <div>
                <div style={{ marginBottom: 8 }}>
                  <span style={s.dot(stateColor(pipStatus.state))} />
                  <span style={{ fontWeight: 600, fontSize: 15, color: '#f1f5f9' }}>{pipStatus.state?.toUpperCase()}</span>
                </div>
                {pipStatus.started  && <div style={{ fontSize: 12, color: '#64748b' }}>Started:  {new Date(pipStatus.started).toLocaleString()}</div>}
                {pipStatus.ended    && <div style={{ fontSize: 12, color: '#64748b' }}>Finished: {new Date(pipStatus.ended).toLocaleString()}</div>}
                {pipStatus.run_id   && <div style={{ fontSize: 11, color: '#334155', marginTop: 6 }}>{pipStatus.run_id}</div>}
              </div>
            )}
            {!pipStatus?.available && (
              <div style={{ color: '#f59e0b', fontSize: 13 }}>
                Airflow not reachable — run: <code style={{ color: '#94a3b8' }}>docker compose up -d</code>
              </div>
            )}
          </div>

          {/* Trigger */}
          <div style={{ background: '#0f172a', borderRadius: 10, padding: 20 }}>
            <div style={{ fontSize: 12, color: '#64748b', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>Manual Trigger</div>
            <div style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
              Fires: Extract API → Stage PostgreSQL → PySpark Star Schema
            </div>
            <button style={{ ...s.btn('primary'), width: '100%', opacity: triggering ? 0.6 : 1 }}
                    onClick={triggerPipeline} disabled={triggering}>
              {triggering ? '⏳ Triggering…' : '▶ Run tunigoal_pipeline'}
            </button>
            {trigMsg && (
              <div style={{ marginTop: 12, fontSize: 12, color: trigMsg.ok ? '#10b981' : '#f59e0b', lineHeight: 1.5 }}>
                {trigMsg.text}
              </div>
            )}
          </div>
        </div>

        {/* Pipeline stages */}
        <div style={{ marginTop: 20, display: 'flex', gap: 0 }}>
          {[
            { label: 'Extract', desc: 'api-sports.io → JSON' },
            { label: 'Stage',   desc: 'JSON → raw_matches' },
            { label: 'Spark',   desc: 'DQ + Star Schema' },
            { label: 'Serve',   desc: 'React Dashboard' },
          ].map((step, i, arr) => (
            <div key={step.label} style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
              <div style={{ flex: 1, textAlign: 'center', padding: '10px 8px',
                background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)',
                borderRadius: 8, fontSize: 12 }}>
                <div style={{ color: '#10b981', fontWeight: 700 }}>{step.label}</div>
                <div style={{ color: '#475569', marginTop: 2 }}>{step.desc}</div>
              </div>
              {i < arr.length - 1 && <div style={{ color: '#334155', padding: '0 4px', fontSize: 18 }}>→</div>}
            </div>
          ))}
        </div>

        {warehouse && (
          <div style={{ marginTop: 16, fontSize: 12, color: '#475569' }}>
            <span style={{ marginRight: 24 }}>Staging: {warehouse.raw_matches} matches</span>
            <span style={{ marginRight: 24 }}>Gold: {warehouse.gold_layer_built ? '✅ Built' : '⚠️ Not built — run pipeline to build star schema'}</span>
          </div>
        )}
      </div>

      {/* Recent matches */}
      <div style={s.card}>
        <div style={{ ...s.sectionTitle, marginBottom: 20 }}><span style={s.accent}>//</span> Recent Ligue Pro 1 Results</div>
        <table style={s.table}>
          <thead><tr>
            <th style={s.th}>Date</th>
            <th style={s.th}>Home</th>
            <th style={{ ...s.th, textAlign: 'center' }}>Score</th>
            <th style={s.th}>Away</th>
          </tr></thead>
          <tbody>
            {matches.map(m => (
              <tr key={m.id}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(16,185,129,0.04)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <td style={{ ...s.td, color: '#475569', fontSize: 12 }}>{m.date}</td>
                <td style={{ ...s.td, color: '#f1f5f9', fontWeight: 500 }}>{m.home}</td>
                <td style={{ ...s.td, textAlign: 'center', fontWeight: 700,
                  color: m.hg > m.ag ? '#10b981' : m.hg < m.ag ? '#ef4444' : '#eab308' }}>
                  {m.hg} – {m.ag}
                </td>
                <td style={{ ...s.td, color: '#f1f5f9', fontWeight: 500 }}>{m.away}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Analytics Tab ─────────────────────────────────────────────────────────────
function AnalyticsTab() {
  const [standings, setStandings] = useState([])
  const [scorers,   setScorers]   = useState([])

  useEffect(() => {
    api('/standings').then(d => { if (d) setStandings(d) })
    api('/scorers').then(d => { if (d) setScorers(d) })
  }, [])

  return (
    <div style={{ display: 'grid', gap: 24 }}>
      <div style={s.card}>
        <div style={{ ...s.sectionTitle, marginBottom: 20 }}><span style={s.accent}>//</span> Ligue Pro 1 Standings — 2024/25</div>
        <table style={s.table}>
          <thead><tr>
            {['#', 'Club', 'P', 'W', 'D', 'L', 'GD', 'PTS'].map(h => <th key={h} style={s.th}>{h}</th>)}
          </tr></thead>
          <tbody>
            {standings.map(row => (
              <tr key={row.team}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(16,185,129,0.05)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <td style={{ ...s.td, color: '#475569', width: 32 }}>{row.pos}</td>
                <td style={{ ...s.td, color: '#f1f5f9', fontWeight: 500 }}>
                  {row.pos <= 3 && <span style={s.dot('green')} />}
                  {row.team}
                </td>
                <td style={s.td}>{row.p}</td>
                <td style={{ ...s.td, color: '#10b981' }}>{row.w}</td>
                <td style={{ ...s.td, color: '#eab308' }}>{row.d}</td>
                <td style={{ ...s.td, color: '#ef4444' }}>{row.l}</td>
                <td style={s.td}>{row.gd}</td>
                <td style={{ ...s.td, fontWeight: 700, color: '#f1f5f9' }}>{row.pts}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={s.card}>
        <div style={{ ...s.sectionTitle, marginBottom: 20 }}><span style={s.accent}>//</span> Top Scorers — 2024/25</div>
        {scorers.length === 0 ? (
          <div style={{ color: '#64748b', fontSize: 14 }}>Scorer data loaded from api-sports.io.</div>
        ) : (
          <table style={s.table}>
            <thead><tr>
              {['#', 'Player', 'Club', 'Goals', 'Assists', 'Apps'].map(h => <th key={h} style={s.th}>{h}</th>)}
            </tr></thead>
            <tbody>
              {scorers.map(p => (
                <tr key={p.name}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(16,185,129,0.05)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                  <td style={{ ...s.td, color: '#475569' }}>{p.rank}</td>
                  <td style={{ ...s.td, color: '#f1f5f9', fontWeight: 500 }}>{p.name}</td>
                  <td style={{ ...s.td, color: '#64748b' }}>{p.team}</td>
                  <td style={{ ...s.td, color: '#10b981', fontWeight: 700 }}>{p.goals}</td>
                  <td style={s.td}>{p.assists}</td>
                  <td style={{ ...s.td, color: '#475569' }}>{p.appearances}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

// ── Predictor Tab ─────────────────────────────────────────────────────────────
function PredictorTab() {
  const [teams,    setTeams]    = useState([])
  const [home,     setHome]     = useState('')
  const [away,     setAway]     = useState('')
  const [result,   setResult]   = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [err,      setErr]      = useState(null)

  useEffect(() => {
    api('/teams').then(d => {
      if (d && d.length) {
        setTeams(d)
        setHome(d[0])
        setAway(d[1])
      }
    })
  }, [])

  const predict = async () => {
    if (!home || !away || home === away) { setErr('Select two different teams'); return }
    setLoading(true); setErr(null); setResult(null)
    const r = await api('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ home_team: home, away_team: away })
    })
    setLoading(false)
    if (!r) { setErr('API unreachable'); return }
    setResult(r)
  }

  const pct = (v) => `${(v * 100).toFixed(1)}%`
  const outcomeLabel = (o) => o === 'home_win' ? `${result.home_team} wins` : o === 'away_win' ? `${result.away_team} wins` : 'Draw'
  const barColor  = (k) => k === 'home_win' ? '#10b981' : k === 'away_win' ? '#ef4444' : '#eab308'

  return (
    <div style={{ display: 'grid', gap: 24 }}>
      <div style={s.card}>
        <div style={{ ...s.sectionTitle, marginBottom: 4 }}><span style={s.accent}>//</span> Match Outcome Predictor</div>
        <div style={{ fontSize: 13, color: '#475569', marginBottom: 24 }}>
          Weighted scoring model — win rate 50%, goal avg 30%, head-to-head 12%, home advantage 8%
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 16, alignItems: 'end', marginBottom: 24 }}>
          <div>
            <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>Home Team</div>
            <select style={s.select} value={home} onChange={e => setHome(e.target.value)}>
              {teams.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#334155', paddingBottom: 10 }}>vs</div>
          <div>
            <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>Away Team</div>
            <select style={s.select} value={away} onChange={e => setAway(e.target.value)}>
              {teams.filter(t => t !== home).map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>

        <button style={{ ...s.btn('primary'), opacity: loading ? 0.6 : 1 }}
                onClick={predict} disabled={loading || !home || !away}>
          {loading ? '⏳ Predicting…' : '⚽ Predict Match'}
        </button>
        {err && <div style={{ marginTop: 12, color: '#f59e0b', fontSize: 13 }}>{err}</div>}
      </div>

      {result && (
        <div style={s.card}>
          <div style={{ textAlign: 'center', marginBottom: 28 }}>
            <div style={{ fontSize: 22, fontWeight: 800, color: '#f1f5f9', marginBottom: 8 }}>
              {result.home_team} <span style={{ color: '#334155' }}>vs</span> {result.away_team}
            </div>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#10b981' }}>
              {outcomeLabel(result.outcome)}
            </div>
            <div style={{ fontSize: 14, color: '#64748b', marginTop: 4 }}>
              {pct(result.confidence)} confidence
            </div>
          </div>

          {/* Probability bars */}
          <div style={{ display: 'grid', gap: 14, marginBottom: 28 }}>
            {Object.entries(result.probabilities).map(([key, val]) => (
              <div key={key}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
                  <span style={{ color: '#94a3b8', textTransform: 'capitalize' }}>
                    {key === 'home_win' ? `${result.home_team} Win` : key === 'away_win' ? `${result.away_team} Win` : 'Draw'}
                  </span>
                  <span style={{ fontWeight: 700, color: barColor(key) }}>{pct(val)}</span>
                </div>
                <div style={{ height: 8, background: 'rgba(51,65,85,0.4)', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: pct(val), background: barColor(key), borderRadius: 4, transition: 'width 0.8s ease' }} />
                </div>
              </div>
            ))}
          </div>

          {/* Expected goals */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', textAlign: 'center', gap: 16,
            background: '#0f172a', borderRadius: 10, padding: '20px 24px' }}>
            <div>
              <div style={{ fontSize: 36, fontWeight: 800, color: '#10b981' }}>{result.expected_goals.home}</div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>{result.home_team}</div>
              <div style={{ fontSize: 11, color: '#334155' }}>xG</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', color: '#334155', fontSize: 20, fontWeight: 800 }}>—</div>
            <div>
              <div style={{ fontSize: 36, fontWeight: 800, color: '#ef4444' }}>{result.expected_goals.away}</div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>{result.away_team}</div>
              <div style={{ fontSize: 11, color: '#334155' }}>xG</div>
            </div>
          </div>

          <div style={{ marginTop: 16, fontSize: 11, color: '#334155', textAlign: 'center' }}>
            Model: win_rate×0.50 + goals_avg×0.30 + h2h×0.12 + home_advantage×0.08
          </div>
        </div>
      )}
    </div>
  )
}

// ── About Tab ─────────────────────────────────────────────────────────────────
function AboutTab() {
  const stack = [
    { tech: 'Apache Spark (PySpark)', ver: '3.5.0', role: 'Distributed ELT — DQ gates + Star Schema' },
    { tech: 'Apache Airflow',         ver: '2.8.1', role: 'DAG orchestration — @daily, CeleryExecutor' },
    { tech: 'PostgreSQL 15',          ver: '15',    role: 'Staging raw tables + gold Star Schema warehouse' },
    { tech: 'FastAPI',                ver: '0.115', role: 'REST API — predict, pipeline trigger, data' },
    { tech: 'React 18 + Vite',        ver: '18',    role: 'Analytics dashboard — predictor + pipeline UI' },
    { tech: 'Redis',                  ver: 'latest','role': 'Airflow Celery message broker' },
    { tech: 'api-sports.io',          ver: 'v3',    role: 'Data source — Tunisian Ligue 1 (league=202)' },
    { tech: 'Docker Compose',         ver: 'v2',    role: 'Full containerisation — 8 services' },
  ]

  const pipeline = [
    { step: '1. Extract',   color: '#10b981', desc: 'extract_api.py fetches fixtures, standings, top scorers from api-sports.io v3 (league=202, season=2024). Falls back to 15 sample fixtures when no API key.' },
    { step: '2. Stage',     color: '#06b6d4', desc: 'load_postgres.py bulk-inserts raw JSON into raw_matches, raw_standings, raw_topscorers with ON CONFLICT DO NOTHING idempotency.' },
    { step: '3. Transform', color: '#8b5cf6', desc: 'transform_raw_spark.py runs PySpark on raw_matches: deduplication, null checks, negative-goals rejection, then builds dim_teams, dim_dates, dim_leagues, fact_matches via JDBC.' },
    { step: '4. Delta load', color: '#f59e0b', desc: 'Left-Anti join on match_id ensures zero duplicates across @daily reruns — only truly new records append to fact_matches.' },
    { step: '5. Serve',     color: '#ec4899', desc: 'FastAPI reads from both raw and gold tables. React shows standings, scorers, recent results, pipeline status, and the match outcome predictor.' },
  ]

  return (
    <div style={{ display: 'grid', gap: 24 }}>
      <div style={s.card}>
        <div style={{ ...s.sectionTitle, marginBottom: 20 }}><span style={s.accent}>//</span> ELT Pipeline — How It Works</div>
        {pipeline.map(p => (
          <div key={p.step} style={{ display: 'flex', gap: 16, marginBottom: 20, alignItems: 'flex-start' }}>
            <div style={{ minWidth: 120, fontSize: 12, fontWeight: 700, color: p.color, paddingTop: 2 }}>{p.step}</div>
            <div style={{ fontSize: 14, color: '#94a3b8', lineHeight: 1.6 }}>{p.desc}</div>
          </div>
        ))}
      </div>

      <div style={s.card}>
        <div style={{ ...s.sectionTitle, marginBottom: 20 }}><span style={s.accent}>//</span> Tech Stack</div>
        <table style={s.table}>
          <thead><tr>
            <th style={s.th}>Technology</th><th style={s.th}>Version</th><th style={s.th}>Purpose</th>
          </tr></thead>
          <tbody>
            {stack.map(t => (
              <tr key={t.tech}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(16,185,129,0.05)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <td style={{ ...s.td, color: '#10b981', fontWeight: 500 }}>{t.tech}</td>
                <td style={{ ...s.td, color: '#64748b' }}>{t.ver}</td>
                <td style={{ ...s.td, color: '#94a3b8' }}>{t.role}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={s.card}>
        <div style={{ ...s.sectionTitle, marginBottom: 16 }}><span style={s.accent}>//</span> Quick Commands</div>
        {[
          ['Start everything',     'docker compose up -d'],
          ['Open Airflow',         'http://localhost:8080  (airflow / airflow)'],
          ['Trigger DAG manually', 'Click "Run tunigoal_pipeline" in Dashboard tab'],
          ['Run Spark transform',  'docker compose run --rm airflow-webserver python /opt/airflow/ingestion/transform_raw_spark.py'],
          ['Re-fetch from API',    'docker compose run --rm airflow-webserver python /opt/airflow/ingestion/extract_api.py'],
        ].map(([label, cmd]) => (
          <div key={label} style={{ display: 'flex', gap: 16, marginBottom: 14, alignItems: 'flex-start' }}>
            <span style={{ color: '#10b981', fontWeight: 600, minWidth: 180, fontSize: 13 }}>{label}</span>
            <code style={{ fontSize: 12, color: '#94a3b8', background: '#0f172a', padding: '3px 8px', borderRadius: 4 }}>{cmd}</code>
          </div>
        ))}
      </div>

      <div style={{ ...s.card, textAlign: 'center', padding: '20px 24px' }}>
        <div style={{ fontWeight: 700, color: '#f1f5f9', marginBottom: 6 }}>Rayen Lassoued</div>
        <div style={{ display: 'flex', gap: 20, justifyContent: 'center' }}>
          <a href="https://github.com/rayenx2"              target="_blank" rel="noreferrer" style={{ color: '#10b981', fontSize: 14, textDecoration: 'none' }}>GitHub</a>
          <a href="https://linkedin.com/in/Rayen-Lassoued"  target="_blank" rel="noreferrer" style={{ color: '#10b981', fontSize: 14, textDecoration: 'none' }}>LinkedIn</a>
        </div>
      </div>
    </div>
  )
}

// ── App Shell ─────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState('dashboard')

  return (
    <div style={s.wrap}>
      {/* Top accent bar */}
      <div style={{ height: 2, background: 'linear-gradient(90deg,#10b981,#06b6d4,#8b5cf6)' }} />

      {/* Header */}
      <header style={s.header}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <svg width="36" height="36" viewBox="0 0 100 100" style={{ marginRight: 10, flexShrink: 0 }}>
            {/* Classic black-and-white football */}
            <circle cx="50" cy="50" r="46" fill="white" stroke="#1e293b" strokeWidth="3"/>
            {/* Center pentagon (black) */}
            <polygon points="50,28 63,37 58,52 42,52 37,37" fill="#0f172a"/>
            {/* Top pentagon patch */}
            <polygon points="50,7  61,15 58,28 42,28 39,15" fill="#0f172a"/>
            {/* Top-right patch */}
            <polygon points="72,18 80,31 72,40 63,37 61,23" fill="#0f172a"/>
            {/* Bottom-right patch */}
            <polygon points="76,58 72,72 60,76 52,66 58,52" fill="#0f172a"/>
            {/* Bottom-left patch */}
            <polygon points="24,58 42,52 48,66 40,76 28,72" fill="#0f172a"/>
            {/* Top-left patch */}
            <polygon points="28,18 39,23 37,37 28,40 20,31" fill="#0f172a"/>
            {/* Green accent ring */}
            <circle cx="50" cy="50" r="46" fill="none" stroke="#10b981" strokeWidth="4" opacity="0.6"/>
          </svg>
          <span style={{ fontWeight: 800, fontSize: 18, color: '#f1f5f9' }}>TuniGoal</span>
          <span style={{ fontSize: 13, color: '#475569', marginLeft: 12 }}>Ligue Pro 1 Analytics</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {['PySpark 3.5','Airflow 2.8','PostgreSQL','FastAPI'].map(t => (
            <span key={t} style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4,
              background: 'rgba(51,65,85,0.4)', color: '#64748b', border: '1px solid rgba(51,65,85,0.6)' }}>{t}</span>
          ))}
        </div>
      </header>

      {/* Hero */}
      <div style={s.hero}>
        <div style={s.badge}><span>●</span> Pipeline Active — Tunisian Ligue Pro 1</div>
        <h1 style={{ ...s.heroTitle, marginTop: 20 }}>
          TuniGoal<br /><span style={s.accent}>Data Pipeline</span>
        </h1>
        <p style={s.heroSub}>
          End-to-end ELT pipeline: api-sports.io → PostgreSQL staging → PySpark Star Schema → live analytics
        </p>
      </div>

      {/* Tabs + content */}
      <div style={s.content}>
        <div style={s.tabs}>
          {[
            ['dashboard', 'Dashboard & Pipeline'],
            ['analytics', 'Standings & Scorers'],
            ['predictor', '⚽ Match Predictor'],
            ['about',     'About'],
          ].map(([id, label]) => (
            <button key={id} style={s.tab(tab === id)} onClick={() => setTab(id)}>{label}</button>
          ))}
        </div>

        {tab === 'dashboard' && <DashboardTab />}
        {tab === 'analytics' && <AnalyticsTab />}
        {tab === 'predictor' && <PredictorTab />}
        {tab === 'about'     && <AboutTab />}
      </div>
    </div>
  )
}
