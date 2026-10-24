# Despliegue y seguridad

Esta versión está pensada para ejecución local. **No expongas el endpoint de análisis a Internet** hasta probar aislamiento de red y navegador, limitar recursos por infraestructura y reemplazar el rate limit en memoria.

## Servidor

En Windows local, Waitress sirve WSGI (ver README). En Linux, usa un servidor WSGI mantenido tras un proxy TLS y configura límites de procesos, memoria y tiempo. No uses `app.run(debug=True)` en producción. Mantén `HOST` en loopback detrás del proxy; no habilites debug.

## Variables

Configura `FRONTEND_ORIGINS` con orígenes exactos, nunca `*`. Ajusta `REQUEST_TIMEOUT_SECONDS` y `MAX_RESPONSE_BYTES` según recursos disponibles. `VITE_API_BASE_URL` se fija al compilar el frontend. `.env.example` contiene solo valores no sensibles. No hay claves externas ni persistencia de resultados.

## Controles de salida

El backend permite HTTP/HTTPS solo por los puertos estándar 80/443, rechaza credenciales y nombres locales conocidos, resuelve A/AAAA y exige que todas las direcciones sean globales. Se conecta al socket con una IP validada para mitigar DNS rebinding, verifica certificados TLS, no usa proxies del entorno, limita redirecciones y repite validación por salto. Limita tiempo, cuerpo HTML sin compresión y frecuencia por IP dentro del proceso. No reenvía cookies ni encabezados de usuario, no sigue formularios ni recursos embebidos.

Para producción, configura además reglas de egreso de firewall que bloqueen redes privadas, loopback, link-local y metadata; usa un proxy de salida que vuelva a aplicar esa política. Ejecuta sin privilegios, con aislamiento de proceso/contenedor, límites de CPU/memoria y logs sin URL completa. Evita SSRF indirecto por un resolver/proxy transparente no confiable.

## Limitaciones de endurecimiento

- El limitador actual es local al proceso; puede eludirse con varios workers y su almacenamiento no es compartido.
- No hay aislamiento de navegador porque este MVP no ejecuta Playwright/axe-core ni JavaScript remoto.
- El parser recibe HTML limitado en memoria; dimensiona workers para este máximo y aplica timeout también en proxy/WSGI.
- No se ha incluido configuración Docker: la lista de egreso correcta depende de la plataforma de despliegue.

No almacenes historial, cookies o cuerpo de página. Los reportes omiten los parámetros de consulta de la URL para evitar exportar secretos que alguien haya puesto allí. Revisa cambios en reglas y controles antes de habilitar nuevos protocolos, puertos o capacidades de navegador.
