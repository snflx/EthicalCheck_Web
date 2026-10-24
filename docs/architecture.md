# Arquitectura

```text
React/Vite ── POST /api/v1/analyze ── Flask API
                                          │
                                Pydantic + límite de uso
                                          │
                              URL guard + fetch HTTP fijado
                                          │
                                  HTML (máx. 2 MiB)
                                          │
                         ┌────────────────┼────────────────┐
                    Accesibilidad       Privacidad       Lenguaje
                         └────────────────┼────────────────┘
                                     Puntuación
                                          │
                                  Reporte tipado
```

- `backend/app/api/routes.py`: validación de solicitud, errores, rate limit en proceso, coordinación de analizadores y serialización.
- `backend/app/services/url_guard.py`: normaliza URL, rechaza destinos locales y valida cada IP DNS como global.
- `backend/app/services/fetcher.py`: conecta el socket directamente a una IP ya resuelta; mantiene Host y SNI para TLS, valida certificados y no sigue redirecciones automáticamente.
- `backend/app/analyzers/`: reglas independientes sobre HTML parseado. No envían formularios ni ejecutan JavaScript.
- `backend/app/scoring.py`: pesos y penalizaciones centrales, más cobertura y límite máximo de puntuación.
- `backend/app/schemas/report.py`: contrato de entrada/salida.
- `frontend/src/services/api.ts`: cliente central. `types.ts` refleja el reporte del backend; `App.tsx` muestra el reporte y exporta JSON/CSV.

La evaluación es síncrona y de una sola página. La interfaz separa estado de carga, error y resultado. La puntuación usa dimensión (50 % accesibilidad, 30 % privacidad, 20 % lenguaje), resta 18 por hallazgo de error, 9 por advertencia y 4 por revisión sugerida, y se limita a 95. Una dimensión sin reglas evaluables carece de puntuación. Cobertura se informa aparte.

## Límites actuales

Playwright y axe-core no forman parte de esta versión. Contraste, comportamiento del teclado y auditoría completa de ARIA se identifican como no evaluados. Si una regla no puede medirse, no se computa como aprobada ni como fallo.
