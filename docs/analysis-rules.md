# Reglas de análisis y puntuación

El motor 1.0.0 analiza una única respuesta HTML de una URL pública. Los estados son `pass`, `fail`, `review`, `not_evaluated` y `not_applicable`; los hallazgos distinguen evidencia confirmada de sugerencias posibles.

## Accesibilidad (50 %)

| Regla | Comprobación |
|---|---|
| A11Y-IMG-ALT | Imágenes sin atributo `alt`; posible incidencia hasta revisar si es decorativa. `alt=""` se acepta. |
| A11Y-FORM-LABEL | Campos con label, label envolvente o nombre ARIA. |
| A11Y-NAME | Botones/enlaces sin texto ni nombre accesible detectado. |
| A11Y-LANG | Atributo `lang` en `<html>`. |
| A11Y-HEADING-ORDER | Saltos de niveles consecutivos observables en el HTML. |
| A11Y-CONTRAST | No evaluada: requiere estilos computados. |
| A11Y-ARIA | No evaluada: validación completa requiere DOM activo/axe-core. |
| A11Y-KEYBOARD | No evaluada: no se interactúa con teclado. |

## Privacidad y transparencia (30 %)

Se buscan términos y enlaces visibles para `PRIVACY-POLICY`, `PRIVACY-TERMS`, `PRIVACY-COOKIES` y `PRIVACY-CONTACT`. Una referencia hallada solo confirma su presencia, no su calidad ni conformidad legal. `PRIVACY-PERSONAL-FORM` señala campos cuyos atributos sugieren que piden datos personales, para revisión contextual. `PRIVACY-FORM-HTTPS` identifica formularios que parecen transmitir datos por HTTP. `PRIVACY-HTTPS` observa el esquema de la página. `PRIVACY-CONSENT` puede detectar texto de consentimiento visible, pero no valida su funcionamiento; no se aceptan cookies ni se cambian preferencias.

## Lenguaje (20 %)

`LANG-REVIEW` localiza expresiones del diccionario configurable `analyzers/language_rules.py`. Cada coincidencia se etiqueta como revisión posible y muestra un fragmento y alternativa sugerida. No determina intención ni reemplaza revisión humana.

## Puntuación

Por dimensión, se parte de 100 y se restan 18 puntos por hallazgo `error`, 9 por `warning` y 4 por `review`; la dimensión se limita a 1–95. Sin reglas evaluables, la puntuación es `null`. La puntuación global es el promedio ponderado de dimensiones disponibles con pesos 0.50, 0.30 y 0.20 renormalizados. El tope de 95 evita presentar perfección automática. Los hallazgos sugeridos también descuentan modestamente: el indicador es preliminar.

La cobertura es reglas con estado pass/fail/review sobre reglas examinadas, ponderadas por cantidad de reglas, sin incluir reglas no evaluadas. La cobertura baja de 90 % lleva estado parcial y etiqueta de evaluación incompleta. Rangos orientativos: 80–95 buen resultado automatizado, 60–79 requiere mejoras, 1–59 problemas detectados. No son niveles oficiales.
