import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { analyzeSite } from './services/api'
import type { Finding, Report } from './types'

const categoryNames = { accessibility: 'Accesibilidad', privacy: 'Privacidad', language: 'Lenguaje' }
const severityNames = { error: 'Problema', warning: 'Advertencia', review: 'Revisión', info: 'Información' }

function safeFilename(url: string) {
  try { return new URL(url).hostname.replace(/[^a-z0-9.-]/gi, '_') } catch { return 'ethicalcheck' }
}
function download(name: string, content: string, type: string) {
  const blob = new Blob([content], { type })
  const href = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = href; anchor.download = name; anchor.click()
  window.setTimeout(() => URL.revokeObjectURL(href), 1000)
}
function csvCell(value: unknown) {
  let text = String(value ?? '')
  if (/^[\s]*[=+@\-]/.test(text)) text = `'${text}`
  return `"${text.replaceAll('"', '""')}"`
}
function exportCsv(report: Report) {
  const headers = ['Categoría', 'Severidad', 'Hallazgo', 'Descripción', 'Evidencia', 'Selector', 'Recomendación', 'Regla', 'Verificación']
  const rows = report.findings.map(f => [categoryNames[f.category], severityNames[f.severity], f.title, f.description, f.evidence, f.selector, f.recommendation, f.rule_id, f.verification])
  download(`ethicalcheck-${safeFilename(report.analyzed_url)}.csv`, [headers, ...rows].map(row => row.map(csvCell).join(',')).join('\r\n'), 'text/csv;charset=utf-8')
}
function validateUrl(value: string) {
  try {
    const url = new URL(value.trim())
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return false
    const hostname = url.hostname.toLowerCase()
    if (hostname === 'localhost' || hostname.endsWith('.localhost') || hostname.endsWith('.local') || hostname.endsWith('.internal')) return false
    return hostname.includes('.') || hostname.startsWith('[')
  } catch { return false }
}

export default function App() {
  const [url, setUrl] = useState('')
  const [report, setReport] = useState<Report | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [category, setCategory] = useState('all')
  const [severity, setSeverity] = useState('all')
  const [controller, setController] = useState<AbortController | null>(null)
  const visibleFindings = useMemo(() => report?.findings.filter(f => (category === 'all' || f.category === category) && (severity === 'all' || f.severity === severity)) ?? [], [report, category, severity])

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setReport(null)
    const normalized = url.trim()
    if (!validateUrl(normalized)) { setError('Escribe una URL pública válida con http:// o https:// y sin credenciales.'); return }
    const next = new AbortController(); setController(next); setBusy(true)
    try { setReport(await analyzeSite(normalized, next.signal)) }
    catch (exception) { if (!next.signal.aborted) setError(exception instanceof Error ? exception.message : 'No fue posible analizar el sitio. Comprueba la dirección e inténtalo de nuevo.') }
    finally { setBusy(false); setController(null) }
  }

  function reset() { controller?.abort(); setBusy(false); setReport(null); setError(''); setCategory('all'); setSeverity('all') }

  return <div className="app-shell min-h-screen">
    <header className="topbar"><a className="brand" href="#inicio" onClick={reset} aria-label="EthicalCheck Web, volver al inicio"><span className="brand-mark">e<span>·</span></span><span>ethicalcheck<small>WEB AUDIT TOOL</small></span></a><div className="topbar-right"><span className="privacy-chip"><i />Sin historial de análisis</span><a className="top-link" href="#metodo">Cómo evaluamos <span aria-hidden="true">↗</span></a></div></header>
    <main id="inicio">
      {!report ? <section className="hero-grid"><div className="hero-copy"><div className="eyebrow"><span className="eyebrow-line" />AUDITORÍA DIGITAL RESPONSABLE</div><h1>La calidad web también se <em>mide</em>.</h1><p className="hero-intro">Una revisión clara de accesibilidad, transparencia y lenguaje para ayudarte a construir sitios mejores para todas las personas.</p>
        <form onSubmit={submit} className="analyze-form" noValidate><label htmlFor="site-url">URL del sitio web</label><div className="input-row"><span aria-hidden="true" className="input-icon">↗</span><input id="site-url" value={url} onChange={e => setUrl(e.target.value)} placeholder="https://ejemplo.com" type="url" autoComplete="url" aria-describedby={error ? 'url-error' : 'url-hint'} disabled={busy} /><button type="submit" disabled={busy}>{busy ? 'Analizando…' : <>Analizar sitio <span aria-hidden="true">→</span></>}</button></div><p id={error ? 'url-error' : 'url-hint'} className={error ? 'form-error' : 'input-hint'} role={error ? 'alert' : undefined}>{error || 'Solo analizamos páginas públicas. No se envían formularios ni se modifican preferencias.'}</p></form>
        {busy && <div className="progress-card" role="status" aria-live="polite"><div className="progress-spinner"/><div><strong>Analizando la página pública</strong><span>El análisis puede tardar unos segundos.</span></div><button className="cancel-button" onClick={() => controller?.abort()}>Cancelar</button></div>}
        <div className="scope-note"><span className="scope-icon">i</span><p>Analiza solo sitios públicos para los que tengas autorización. Los resultados son orientativos y no constituyen una certificación.</p></div>
      </div><div className="hero-visual"><div className="visual-orbit orbit-one"/><div className="visual-orbit orbit-two"/><div className="audit-card"><div className="audit-card-top"><span>ETHICALCHECK / 01</span><span className="live-dot"/> <span>PREVIEW</span></div><div className="visual-score"><span className="score-dash"/><div><span className="score-placeholder">— —</span><span className="score-caption">PUNTUACIÓN ÉTICA</span></div></div><div className="visual-rule"/><div className="preview-dimensions"><div><span className="dim-icon access-icon">◉</span><span>Accesibilidad</span><b>01</b></div><div><span className="dim-icon privacy-icon">◈</span><span>Privacidad</span><b>02</b></div><div><span className="dim-icon language-icon">Aa</span><span>Lenguaje</span><b>03</b></div></div><div className="audit-stamp"><span>EC</span><span>REVISIÓN<br/>PRELIMINAR</span></div></div><div className="visual-caption"><span>01 — 03</span><span>TRES DIMENSIONES · UNA VISTA</span></div></div>
      <div className="feature-strip"><div><span>01</span><b>Accesibilidad</b><small>Etiquetas, estructura y controles</small></div><div><span>02</span><b>Privacidad</b><small>Transparencia y transporte seguro</small></div><div><span>03</span><b>Lenguaje</b><small>Sugerencias para revisar contexto</small></div><div className="strip-responsible"><span className="lock-icon">⌑</span><span><b>Uso responsable</b><small>Solo páginas públicas · sin almacenamiento</small></span></div></div>
      </section> : <ReportView report={report} findings={visibleFindings} category={category} severity={severity} setCategory={setCategory} setSeverity={setSeverity} onReset={reset} onJson={() => download(`ethicalcheck-${safeFilename(report.analyzed_url)}.json`, JSON.stringify(report, null, 2), 'application/json')} onCsv={() => exportCsv(report)} />}
    </main>
    <footer id="metodo"><div><span className="footer-brand">ethicalcheck<span>·</span></span><span>Un punto de partida para una web más consciente.</span></div><p>La automatización no sustituye una revisión experta.</p><span className="footer-meta">MOTOR V1.0.0 <i/> BOGOTÁ, CO</span></footer>
  </div>
}

function ReportView({ report, findings, category, severity, setCategory, setSeverity, onReset, onJson, onCsv }: {
  report: Report; findings: Finding[]; category: string; severity: string; setCategory: (v: string) => void; setSeverity: (v: string) => void; onReset: () => void; onJson: () => void; onCsv: () => void
}) {
  const tone = report.score === null ? 'neutral' : report.score >= 80 ? 'good' : report.score >= 60 ? 'caution' : 'poor'
  return <section className="report-page"><div className="report-heading"><div><button className="back-button" onClick={onReset}>← Nueva evaluación</button><div className="eyebrow"><span className="eyebrow-line"/>REPORTE DE ANÁLISIS</div><h1>Una mirada más <em>consciente.</em></h1></div><div className="export-actions"><button onClick={onJson}>↓ JSON</button><button onClick={onCsv}>↓ CSV</button></div></div>
    <div className="report-meta"><span className="report-url">↗ {report.analyzed_url}</span><span>{new Date(report.analyzed_at).toLocaleString('es-CO')}</span><span className={`status-tag ${report.status}`}>{report.status === 'partial' ? 'Evaluación incompleta' : 'Completada'}</span></div>
    <div className={`score-panel ${tone}`}><div className="score-number">{report.score ?? '—'}<small>/100</small></div><div className="score-info"><span className="eyebrow">SEMÁFORO ÉTICO · INDICADOR INTERNO</span><h2>{report.score_label}</h2><p>Una señal orientativa, nunca una certificación.</p></div><div className="coverage"><span>{report.coverage_percent}%</span><small>COBERTURA DE<br/>REGLAS EVALUABLES</small></div></div>
    <div className="dimension-grid">{report.dimensions.map(d => <article className="dimension-card" key={d.id}><div className="dimension-head"><span className={`dimension-mark ${d.id}`}>{d.id === 'accessibility' ? '◉' : d.id === 'privacy' ? '◈' : 'Aa'}</span><span>{String(d.id).padStart(2, '0')}</span></div><h3>{d.name}</h3><div className="dimension-score">{d.score ?? '—'}<small>{d.score === null ? 'sin puntuación' : '/100'}</small></div><div className="dimension-footer"><span>{d.findings_count} hallazgos</span><span>{d.evaluated_rules}/{d.total_rules} reglas</span></div><div className="mini-track"><i style={{ width: `${d.coverage_percent}%` }}/></div></article>)}</div>
    <div className="findings-heading"><div><div className="eyebrow"><span className="eyebrow-line"/>EVIDENCIA</div><h2>Hallazgos <span>{report.findings.length.toString().padStart(2, '0')}</span></h2></div><div className="filters"><label>Categoría<select value={category} onChange={e => setCategory(e.target.value)}><option value="all">Todas</option><option value="accessibility">Accesibilidad</option><option value="privacy">Privacidad</option><option value="language">Lenguaje</option></select></label><label>Severidad<select value={severity} onChange={e => setSeverity(e.target.value)}><option value="all">Todas</option><option value="error">Problema</option><option value="warning">Advertencia</option><option value="review">Revisión</option><option value="info">Información</option></select></label></div></div>
    <div className="finding-list">{findings.length ? findings.map(f => <article className="finding" key={f.id}><div className="finding-index">{String(report.findings.indexOf(f) + 1).padStart(2, '0')}</div><div className="finding-main"><div className="finding-tags"><span>{categoryNames[f.category]}</span><span className={`severity ${f.severity}`}>{severityNames[f.severity]}</span></div><h3>{f.title}</h3><p>{f.description}</p><blockquote>{f.evidence}</blockquote>{f.selector && <code>{f.selector}</code>}<div className="recommendation"><span>↳</span><p>{f.recommendation}</p></div><div className="rule-meta">REGLA {f.rule_id} <i/> {f.verification === 'possible' ? 'REQUIERE REVISIÓN' : 'EVIDENCIA VERIFICABLE'}</div></div></article>) : <div className="empty-state">No hay hallazgos para estos filtros.</div>}</div>
    <aside className="limitations"><div className="limitations-mark">i</div><div><h3>Alcance y limitaciones</h3><ul>{report.limitations.map(item => <li key={item}>{item}</li>)}</ul></div></aside>
  </section>
}
