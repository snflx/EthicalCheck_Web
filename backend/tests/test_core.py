import pytest
from unittest.mock import patch

from app import create_app
from app.analyzers.accessibility import analyze_accessibility
from app.analyzers.privacy import analyze_privacy
from app.analyzers.language import analyze_language
from app.scoring import build_dimensions
from app.services.url_guard import URLRejected, checked_redirect, normalize_url, resolve_public
from bs4 import BeautifulSoup


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.com", "http://localhost", "http://user:pass@example.com", "http://host.local", "http://example.com:8080"])
def test_rejects_invalid_or_internal_urls(url):
    with pytest.raises(URLRejected):
        normalize_url(url)


def test_normalizes_public_url_and_blocks_private_ip():
    assert normalize_url("HTTPS://example.com/path#fragment") == "https://example.com/path"
    for address in ("::1", "127.0.0.1"):
        with pytest.raises(URLRejected):
            resolve_public(address)


def test_redirect_to_private_destination_is_rejected():
    with pytest.raises(URLRejected):
        checked_redirect("https://example.com/", "http://169.254.169.254/latest/meta-data/")


def test_accessibility_evidence_for_missing_alt_label_and_language():
    soup = BeautifulSoup('<html><body><img src="x.png"><input id="email"><h1>Hola</h1></body></html>', "html.parser")
    findings, rules = analyze_accessibility(soup)
    assert {"A11Y-IMG-ALT", "A11Y-FORM-LABEL", "A11Y-LANG"}.issubset({f["rule_id"] for f in findings})
    assert any(rule["status"] == "not_evaluated" for rule in rules)


def test_privacy_links_and_http_form():
    soup = BeautifulSoup('<a href="/privacidad">Privacidad</a><form action="http://example.com/submit" method="post"></form>', "html.parser")
    findings, rules = analyze_privacy(soup, "http://example.com")
    assert next(r for r in rules if r["id"] == "PRIVACY-POLICY")["status"] == "pass"
    assert any(f["rule_id"] == "PRIVACY-FORM-HTTPS" for f in findings)


def test_language_rule_is_review_not_violation():
    findings, rules = analyze_language(BeautifulSoup("<p>Los usuarios acceden al sistema</p>", "html.parser"))
    assert findings and findings[0]["verification"] == "possible"
    assert rules[0]["status"] == "review"


def test_scoring_is_bounded_and_exposes_coverage():
    results = {"findings": [], "accessibility": [{"id": "a", "status": "pass", "evidence": "ok"}],
        "privacy": [{"id": "p", "status": "not_evaluated", "evidence": "n/a"}],
        "language": [{"id": "l", "status": "review", "evidence": "review"}]}
    dimensions, score, coverage = build_dimensions(results)
    assert 1 <= score <= 95
    assert coverage == 67
    assert dimensions[1]["score"] is None


def test_api_health_rules_invalid_url_and_rate_limit():
    app = create_app({"TESTING": True, "MAX_ANALYSES_PER_MINUTE": 1})
    client = app.test_client()
    assert client.get("/api/v1/health").json["status"] == "ok"
    assert client.get("/api/v1/rules").status_code == 200
    assert client.post("/api/v1/analyze", json={"url": "file:///tmp/a"}).status_code == 400
    assert client.post("/api/v1/analyze", json={"url": "http://127.0.0.1"}).status_code == 429


def test_api_report_is_partial_and_omits_query_parameters():
    app = create_app({"TESTING": True, "MAX_ANALYSES_PER_MINUTE": 100})
    with patch("app.api.routes.fetch_html", return_value=("https://example.com/account?token=secret", "<html lang='es'><body><h1>Hola</h1></body></html>")):
        response = app.test_client().post("/api/v1/analyze", json={"url": "https://example.com/account?token=secret"})
    assert response.status_code == 200
    assert response.json["analyzed_url"] == "https://example.com/account"
    assert response.json["status"] == "partial"
    assert all(rule["status"] in {"pass", "fail", "review", "not_evaluated", "not_applicable"}
               for dimension in response.json["dimensions"] for rule in dimension["rules"])


def test_api_keeps_other_dimensions_when_one_analyzer_fails():
    app = create_app({"TESTING": True, "MAX_ANALYSES_PER_MINUTE": 100})
    with patch("app.api.routes.fetch_html", return_value=("https://example.com/", "<html lang='es'><body>Hola</body></html>")), \
         patch("app.api.routes.analyze_accessibility", side_effect=RuntimeError("internal detail")):
        response = app.test_client().post("/api/v1/analyze", json={"url": "https://example.com/"})
    assert response.status_code == 200
    assert response.json["status"] == "partial"
    assert response.json["dimensions"][0]["score"] is None
    assert response.json["dimensions"][1]["score"] is not None
