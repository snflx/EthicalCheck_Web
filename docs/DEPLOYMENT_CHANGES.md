# Cambios realizados para despliegue en GitHub Pages

## Fecha
24 de octubre de 2026

## Objetivo
Adaptar EthicalCheck Web para que pueda desplegarse como sitio estático en GitHub Pages. Dado que GitHub Pages solo sirve archivos estáticos y no puede ejecutar el backend Flask, se implementó un **modo demo** para mantener la funcionalidad visual y demostrativa.

## Cambios en frontend

### `frontend/vite.config.ts`
- Cambiado `base` de configuración por defecto a `./` para rutas relativas
- Configurado `build.outDir` a `../docs` para compilar directamente a la carpeta `docs/`
- Habilitado `build.emptyOutDir: true` para limpiar la carpeta antes de compilar

### `frontend/src/services/api.ts`
- Añadido detección automática de GitHub Pages (`hostname.endsWith('github.io')`)
- Implementado **modo demo** cuando:
  - Se ejecuta en GitHub Pages
  - No hay `VITE_API_BASE_URL` configurado
- Creada función `generateDemoReport()` que genera un reporte simulado completo con:
  - 3 dimensiones (Accesibilidad, Privacidad, Lenguaje)
  - Hallazgos de ejemplo por categoría
  - Puntuación, cobertura y limitaciones
  - Mismos tipos y estructura que el backend real
- Simulación de latencia (900ms) para mantener experiencia realista
- Soporte para cancelar análisis con `AbortSignal`
- Si hay backend configurado, mantiene el comportamiento original

### `frontend/index.html`
- Generado automáticamente por Vite con rutas relativas `./assets/...`

## Cambios en despliegue

### Carpeta `docs/`
- Generados archivos estáticos: `index.html`, `404.html`, `.nojekyll`
- Assets compilados en `docs/assets/`
- `404.html` copiado desde `index.html` para soporte de SPA routing

### `.nojekyll`
- Añadido archivo vacío para deshabilitar el procesamiento Jekyll de GitHub Pages

### Workflow eliminado
- Eliminado `.github/workflows/deploy-pages.yml` (no necesario con despliegue desde rama `/docs`)

## Configuración de GitHub Pages

Para desplegar correctamente:
1. Ir a **Settings → Pages** del repositorio
2. Source: **Deploy from a branch**
3. Branch: **main**
4. Folder: **/docs**
5. Guardar

URL de despliegue: `https://snflx.github.io/EthicalCheck_Web/`

## Modo demo vs modo real

| Aspecto | Modo Demo (GitHub Pages) | Modo Real (con backend) |
|---|---|---|
| Backend | No requiere | Requiere Flask corriendo |
| Análisis | Simulado | Análisis real con BeautifulSoup + validación SSRF |
| Velocidad | 900ms simulado | Depende del sitio objetivo |
| Datos | Predefinidos | Extraídos del HTML real |
| Configuración | Automático | Requiere `VITE_API_BASE_URL` |

## Comandos para regenerar

```bash
cd frontend
npm install
npx vite build
cp index.html ../docs/404.html  # Ya se hace automáticamente
```

## Notas
- El backend completo sigue intacto en `backend/` para despliegue local o en servidor propio
- Todos los cambios son compatibles con el flujo local existente
- El modo demo es claramente identificado en las limitaciones del reporte
