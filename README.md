# EthicalCheck Web

EthicalCheck Web es un MVP de evaluación preliminar de accesibilidad, privacidad/transparencia y lenguaje inclusivo en una página pública. Presenta puntuaciones auditables, cobertura, evidencia y recomendaciones. **No es una certificación WCAG ni una evaluación legal.**

## Funcionalidades

- Interfaz responsive en React, TypeScript, Vite y Tailwind CSS.
- API Flask versionada para salud, reglas y análisis síncrono.
- Auditoría HTML estática: textos alternativos ausentes, etiquetas de formularios, nombres de controles, idioma, jerarquía de encabezados, indicios de privacidad, formularios HTTP, HTTPS y vocabulario para revisión contextual.
- Resultados parciales identificados, reglas no evaluadas, puntuación limitada a 95 y cobertura visible.
- Filtros por categoría/severidad y exportación JSON/CSV.
- Validación de URL y solicitudes HTTP con IP pública fijada, TLS verificado, redirecciones revalidadas, tiempo/tamaño limitados y sin envío de formularios.

El MVP no integra aún Playwright ni axe-core. Por tanto, las reglas que necesitan estilos computados, interacción de teclado o DOM activo quedan explícitamente como no evaluadas. No se debe desplegar como un servicio público multiusuario sin reforzar el aislamiento del navegador, la limitación de uso distribuida y el control de egreso de red.

## Tecnologías

- Python 3.12+, Flask, Flask-CORS, Pydantic, BeautifulSoup y pytest.
- React 19, TypeScript, Vite y Tailwind CSS 4.
- Waitress como servidor WSGI multiplataforma.

## Requisitos y estructura

Requisitos: Python 3.12 o compatible, Node.js 20.19+ (o 22.12+) y npm. No se descarga ni ejecuta contenido del sitio analizado.

```text
backend/app/       API, analizadores, validación de URL y puntuación
backend/tests/     pruebas unitarias y de API
frontend/src/      interfaz, tipos y cliente HTTP
docs/              arquitectura, reglas y despliegue
```

## Instalación en Windows (PowerShell)

Desde la carpeta del proyecto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
Set-Location frontend
npm install
Set-Location ..
```

Si PowerShell bloquea la activación, usa `\.venv\Scripts\python.exe` y `\.venv\Scripts\pip.exe` directamente. `.env` se lee desde la raíz del proyecto; copia el ejemplo solo si deseas personalizar configuración. No guardes secretos en ese archivo.

## Ejecución local

Terminal 1, desde la raíz:

```powershell
.\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:5000 --call backend.wsgi:application
```

Terminal 2:

```powershell
Set-Location frontend
npm run dev
```

Abre `http://127.0.0.1:5173`. Para otra API, define `VITE_API_BASE_URL` al iniciar Vite, incluyendo `/api/v1`.

## Pruebas y compilación

Desde la raíz, con el entorno virtual activo:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend')
python -m pytest backend\tests -q
Set-Location frontend
npm test
npm run build
```

Las pruebas se ejecutan sin acceder a páginas públicas. No necesitan instalar navegadores.

## Configuración

Variables disponibles (valores de ejemplo en `.env.example`):

| Variable | Uso |
|---|---|
| `HOST`, `PORT` | Dirección local y puerto de Flask/Waitress |
| `FRONTEND_ORIGINS` | Lista separada por comas de orígenes CORS permitidos |
| `MAX_ANALYSES_PER_MINUTE` | Límite por dirección cliente en este proceso |
| `REQUEST_TIMEOUT_SECONDS` | Tiempo máximo por solicitud de destino (2–15 s) |
| `MAX_RESPONSE_BYTES` | Tamaño máximo de HTML (16 KiB–2 MiB) |
| `VITE_API_BASE_URL` | URL del backend para el frontend |

## Limitaciones y errores frecuentes

- DNS del sitio inaccesible, TLS inválido, redirección a IP no pública, página no HTML, respuesta HTTP no exitosa o contenido sobre el límite: el análisis falla con un mensaje explícito.
- No sigue enlaces a políticas ni evalúa páginas adicionales. La búsqueda de transparencia se limita al HTML descargado.
- La URL exportada omite los parámetros de consulta para reducir el riesgo de incluir tokens o datos sensibles que se hayan colocado allí.
- La heurística lingüística ofrece sugerencias, no clasifica discriminación.
- El limitador en memoria no comparte estado entre procesos ni servidores.
- La versión actual usa HTML estático y omite comprobaciones que requieren navegador; instalar Playwright por sí solo no habilita axe-core.
- En producción, restringe la red de salida a destinos públicos, ejecuta el servicio con privilegios mínimos, habilita TLS en un proxy de confianza, establece límites a nivel de proxy y sustituye el limitador en memoria por uno compartido.

## Despliegue

Consulta [docs/deployment.md](docs/deployment.md). Antes de ofrecer análisis públicos, añade aislamiento de navegador y controles de egreso probados. No uses el servidor de desarrollo Flask en producción.
