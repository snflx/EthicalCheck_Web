import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from './App'

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

const report = {
  engine_version: '1.0.0', analyzed_url: 'https://example.com/', analyzed_at: '2026-01-01T00:00:00Z',
  status: 'partial' as const, score: 82, score_label: 'Evaluación incompleta', coverage_percent: 75,
  dimensions: [
    { id: 'accessibility', name: 'Accesibilidad', score: 78, findings_count: 1, evaluated_rules: 3, total_rules: 4, coverage_percent: 75, rules: [] },
    { id: 'privacy', name: 'Privacidad y transparencia', score: 90, findings_count: 0, evaluated_rules: 2, total_rules: 3, coverage_percent: 67, rules: [] },
    { id: 'language', name: 'Lenguaje inclusivo', score: 95, findings_count: 0, evaluated_rules: 1, total_rules: 1, coverage_percent: 100, rules: [] },
  ],
  findings: [{ id: 'A11Y-LANG-1', rule_id: 'A11Y-LANG', category: 'accessibility' as const, title: 'Idioma no declarado', severity: 'warning' as const, description: 'Falta lang.', evidence: '<html>', selector: 'html', recommendation: 'Declara lang="es".', verification: 'confirmed' as const }],
  limitations: ['Evaluación orientativa.'],
}

describe('EthicalCheck Web', () => {
  it('valida la URL antes de llamar a la API', () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    fireEvent.change(screen.getByLabelText('URL del sitio web'), { target: { value: 'file:///etc/passwd' } })
    fireEvent.click(screen.getByRole('button', { name: /analizar sitio/i }))
    expect(screen.getByRole('alert').textContent).toContain('URL pública válida')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('muestra el reporte real y filtra hallazgos por categoría', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => report })
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    fireEvent.change(screen.getByLabelText('URL del sitio web'), { target: { value: 'https://example.com' } })
    fireEvent.click(screen.getByRole('button', { name: /analizar sitio/i }))
    await screen.findByRole('heading', { name: 'Una mirada más consciente.' })
    expect(screen.getByText('82', { exact: true })).toBeTruthy()
    expect(screen.getByText('Idioma no declarado')).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Categoría'), { target: { value: 'privacy' } })
    expect(screen.getByText('No hay hallazgos para estos filtros.')).toBeTruthy()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})
