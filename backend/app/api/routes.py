from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock
import time
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup
from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from ..analyzers import analyze_accessibility, analyze_language, analyze_privacy
from ..schemas.report import AnalyzeRequest, Report
from ..scoring import build_dimensions
from ..services.fetcher import FetchError, fetch_html
from ..services.url_guard import URLRejected, normalize_url

api = Blueprint("api", __name__)
_requests, _lock = defaultdict(deque), Lock()


def _error(message, status, code):
    return jsonify({"error": {"code": code, "message": message}}), status


def _rate_limited():
    key = request.remote_addr or "unknown"
    now = time.monotonic()
    with _lock:
        queue = _requests[key]
        while queue and now - queue[0] > 60:
            queue.popleft()
        if len(queue) >= current_app.config["MAX_ANALYSES_PER_MINUTE"]:
            return True
        queue.append(now)
    return False


@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "ethicalcheck-api", "engine_version": "1.0.0"})


@api.errorhandler(413)
def request_too_large(_error):
    return _error_response("La solicitud supera el tamaño máximo permitido.", 413, "request_too_large")


def _error_response(message, status, code):
    return jsonify({"error": {"code": code, "message": message}}), status


@api.get("/rules")
def rules():
    return jsonify({"categories": ["accessibility", "privacy", "language"], "version": "1.0.0",
        "rules": ["A11Y-IMG-ALT", "A11Y-FORM-LABEL", "A11Y-NAME", "A11Y-LANG", "A11Y-HEADING-ORDER",
                  "A11Y-CONTRAST", "A11Y-ARIA", "A11Y-KEYBOARD", "PRIVACY-POLICY", "PRIVACY-TERMS",
                  "PRIVACY-COOKIES", "PRIVACY-CONTACT", "PRIVACY-FORM-HTTPS", "PRIVACY-HTTPS",
                  "PRIVACY-PERSONAL-FORM", "PRIVACY-CONSENT", "LANG-REVIEW"]})


@api.post("/analyze")
def analyze():
    if _rate_limited():
        return _error("Se alcanzó el límite temporal. Espera un minuto e inténtalo de nuevo.", 429, "rate_limited")
    try:
        payload = AnalyzeRequest.model_validate(request.get_json(silent=True) or {})
        target = normalize_url(str(payload.url))
        final_url, html = fetch_html(target, current_app.config["REQUEST_TIMEOUT_SECONDS"], current_app.config["MAX_RESPONSE_BYTES"])
    except ValidationError:
        return _error("Proporciona una URL HTTP o HTTPS válida, sin credenciales.", 400, "invalid_url")
    except URLRejected as exc:
        return _error(str(exc), 400, "url_blocked")
    except FetchError as exc:
        return _error(str(exc), 422, "target_unavailable")
    except Exception:
        current_app.logger.exception("Unexpected analysis failure")
        return _error("No se pudo completar el análisis por un error interno.", 500, "analysis_failed")

    soup = BeautifulSoup(html, "html.parser")
    analyzer_failed = False
    try:
        accessibility_findings, accessibility_rules = analyze_accessibility(soup)
    except Exception:
        current_app.logger.exception("Accessibility analyzer failure")
        accessibility_findings, accessibility_rules = [], [{"id": "A11Y-ANALYZER", "status": "not_evaluated", "evidence": "El analizador no pudo completar esta dimensión."}]
        analyzer_failed = True
    try:
        privacy_findings, privacy_rules = analyze_privacy(soup, final_url)
    except Exception:
        current_app.logger.exception("Privacy analyzer failure")
        privacy_findings, privacy_rules = [], [{"id": "PRIVACY-ANALYZER", "status": "not_evaluated", "evidence": "El analizador no pudo completar esta dimensión."}]
        analyzer_failed = True
    try:
        language_findings, language_rules = analyze_language(soup)
    except Exception:
        current_app.logger.exception("Language analyzer failure")
        language_findings, language_rules = [], [{"id": "LANG-ANALYZER", "status": "not_evaluated", "evidence": "El analizador no pudo completar esta dimensión."}]
        analyzer_failed = True
    findings = accessibility_findings + privacy_findings + language_findings
    severity_priority = {"error": 0, "warning": 1, "review": 2, "info": 3}
    findings.sort(key=lambda finding: severity_priority[finding["severity"]])
    report_input = {"findings": findings,
        "accessibility": accessibility_rules, "privacy": privacy_rules, "language": language_rules}
    dimensions, score, coverage = build_dimensions(report_input)
    limitations = [
        "El análisis es una evaluación automatizada preliminar y no constituye certificación de accesibilidad ni cumplimiento legal.",
        "La versión actual analiza HTML estático. Contraste computado, validación completa ARIA, interacción de teclado y auditoría axe-core requieren un navegador aislado y quedan sin evaluar.",
        "La revisión lingüística utiliza coincidencias de vocabulario; no determina intención ni contexto semántico.",
        "Solo se analiza una página pública; no se rastrean otras rutas, no se envían formularios ni se alteran preferencias de cookies.",
    ]
    if analyzer_failed:
        limitations.append("Al menos un analizador falló; sus reglas aparecen como no evaluadas y se conservaron los demás resultados.")
    partial = coverage < 90 or analyzer_failed
    parsed_final = urlsplit(final_url)
    report_url = urlunsplit((parsed_final.scheme, parsed_final.netloc, parsed_final.path, "", ""))
    report = Report(engine_version="1.0.0", analyzed_url=report_url, analyzed_at=datetime.now(timezone.utc).isoformat(),
        status="partial" if partial else "completed", score=score,
        score_label="Evaluación incompleta" if partial else ("Buen resultado automatizado" if score >= 80 else "Requiere mejoras" if score >= 60 else "Se detectaron problemas"),
        coverage_percent=coverage, dimensions=dimensions, findings=findings, limitations=limitations)
    return jsonify(report.model_dump()), 200
