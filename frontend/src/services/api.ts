import type { Report } from '../types'

const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const isGitHubPages = typeof window !== 'undefined' && window.location.hostname.endsWith('github.io')
const DEMO_MODE = isGitHubPages || !base

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

function generateDemoReport(url: string): Report {
  const now = new Date().toISOString()
  return {
    engine_version: 'demo-1.0.0',
    analyzed_url: url,
    analyzed_at: now,
    status: 'partial',
    score: 78,
    score_label: 'Bueno - Oportunidades de mejora',
    coverage_percent: 72,
    dimensions: [
      {
        id: 'accessibility',
        name: 'Accesibilidad',
        score: 82,
        findings_count: 2,
        total_rules: 12,
        evaluated_rules: 9,
        coverage_percent: 75,
        rules: []
      },
      {
        id: 'privacy',
        name: 'Privacidad',
        score: 74,
        findings_count: 2,
        total_rules: 8,
        evaluated_rules: 6,
        coverage_percent: 75,
        rules: []
      },
      {
        id: 'language',
        name: 'Lenguaje',
        score: 76,
        findings_count: 1,
        total_rules: 6,
        evaluated_rules: 4,
        coverage_percent: 67,
        rules: []
      }
    ],
    findings: [
      {
        id: 'demo-a11y-1',
        rule_id: 'A11Y-ALT-MISSING',
        category: 'accessibility',
        severity: 'warning',
        title: 'Algunas imágenes podrían carecer de texto alternativo',
        description: 'Se recomienda revisar imágenes informativas para asegurar que cuentan con atributo alt descriptivo.',
        evidence: '<img> sin atributo alt detectado en modo demo.',
        recommendation: 'Añade texto alternativo descriptivo a las imágenes informativas. Usa alt="" para imágenes decorativas.',
        selector: 'img:not([alt])',
        verification: 'possible'
      },
      {
        id: 'demo-a11y-2',
        rule_id: 'A11Y-LABELS',
        category: 'accessibility',
        severity: 'review',
        title: 'Revisar etiquetas de formularios',
        description: 'Algunos controles podrían no estar correctamente asociados a sus etiquetas.',
        evidence: 'Campos de formulario identificados en la estructura.',
        recommendation: 'Asocia cada campo con <label for=...> o usa aria-label cuando sea necesario.',
        selector: 'input, select, textarea',
        verification: 'possible'
      },
      {
        id: 'demo-priv-1',
        rule_id: 'PRIV-HTTPS',
        category: 'privacy',
        severity: 'info',
        title: 'Uso de HTTPS',
        description: 'Se verifica el uso de transporte seguro.',
        evidence: url.startsWith('https://') ? 'La URL utiliza HTTPS.' : 'La URL utiliza HTTP. Se recomienda usar HTTPS.',
        recommendation: 'Usa HTTPS con certificados válidos para proteger la información en tránsito.',
        selector: null,
        verification: 'verifiable'
      },
      {
        id: 'demo-priv-2',
        rule_id: 'PRIV-COOKIES',
        category: 'privacy',
        severity: 'review',
        title: 'Revisar política de cookies/seguimiento',
        description: 'No se ha podido inspeccionar scripts de terceros en modo demo estático.',
        evidence: 'Análisis limitado en modo estático (sin backend).',
        recommendation: 'Revisa si existen terceros, rastreadores o banners de consentimiento.',
        selector: null,
        verification: 'possible'
      },
      {
        id: 'demo-lang-1',
        rule_id: 'LANG-INCLUSIVE',
        category: 'language',
        severity: 'info',
        title: 'Revisión de lenguaje inclusivo',
        description: 'Sugerencias orientativas para un lenguaje más inclusivo.',
        evidence: 'Revisión heurística en modo demo.',
        recommendation: 'Revisa términos de género y fórmulas para promover un lenguaje más inclusivo cuando sea relevante.',
        selector: null,
        verification: 'possible'
      }
    ],
    limitations: [
      'Modo demo en GitHub Pages: sin conexión al backend Flask.',
      'El análisis no descarga ni parsea el HTML real del sitio en este modo estático.',
      'Los resultados son simulados con fines demostrativos.',
      'Para un análisis real, despliega el backend por separado (Render, Railway, Fly.io, etc.) y configura VITE_API_BASE_URL.'
    ]
  }
}

export async function analyzeSite(url: string, signal: AbortSignal): Promise<Report> {
  if (DEMO_MODE) {
    await new Promise(resolve => setTimeout(resolve, 900))
    if (signal.aborted) throw new Error('Análisis cancelado.')
    return generateDemoReport(url)
  }

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
