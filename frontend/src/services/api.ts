import type { Report } from '../types'

const base = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api/v1').replace(/\/$/, '')

function isReport(value: unknown): value is Report {
  if (!value || typeof value !== 'object') return false
  const report = value as Partial<Report>
  return typeof report.engine_version === 'string'
    && typeof report.analyzed_url === 'string'
    && typeof report.analyzed_at === 'string'
    && (report.status === 'completed' || report.status === 'partial')
    && (report.score === null || (typeof report.score === 'number' && report.score >= 1 && report.score <= 100))
    && typeof report.score_label === 'string'
    && typeof report.coverage_percent === 'number' && report.coverage_percent >= 0 && report.coverage_percent <= 100
    && Array.isArray(report.dimensions)
    && report.dimensions.every(d => Boolean(d) && typeof d === 'object' && typeof d.id === 'string' && typeof d.name === 'string' && (d.score === null || (typeof d.score === 'number' && d.score >= 1 && d.score <= 100)) && typeof d.findings_count === 'number' && typeof d.total_rules === 'number' && Array.isArray(d.rules))
    && Array.isArray(report.findings)
    && report.findings.every(f => Boolean(f) && typeof f === 'object' && typeof f.id === 'string' && typeof f.rule_id === 'string' && typeof f.title === 'string' && typeof f.description === 'string' && typeof f.evidence === 'string' && typeof f.recommendation === 'string' && ['accessibility', 'privacy', 'language'].includes(f.category) && ['error', 'warning', 'review', 'info'].includes(f.severity))
    && Array.isArray(report.limitations) && report.limitations.every(item => typeof item === 'string')
}

function responseError(value: unknown) {
  if (value && typeof value === 'object' && 'error' in value) {
    const error = (value as { error?: { message?: unknown } }).error
    if (typeof error?.message === 'string') return error.message
  }
  return 'No fue posible analizar el sitio.'
}

export async function analyzeSite(url: string, signal: AbortSignal): Promise<Report> {
  const timeout = AbortSignal.timeout(15_000)
  const requestSignal = AbortSignal.any([signal, timeout])
  let response: Response
  try {
    response = await fetch(`${base}/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }), signal: requestSignal })
  } catch (error) {
    if (timeout.aborted && !signal.aborted) throw new Error('El servidor tardó demasiado en responder. Puedes intentarlo de nuevo.')
    throw error
  }
  const payload: unknown = await response.json().catch(() => null)
  if (!response.ok) throw new Error(responseError(payload))
  if (!isReport(payload)) throw new Error('El servidor devolvió un reporte incompleto o no válido. Inténtalo de nuevo.')
  return payload
}
