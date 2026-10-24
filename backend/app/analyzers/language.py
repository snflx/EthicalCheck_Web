import re
import unicodedata

from bs4 import BeautifulSoup

from .language_rules import TERMS


def analyze_language(soup: BeautifulSoup):
    for element in soup(["script", "style", "noscript", "svg", "template"]):
        element.decompose()
    text = " ".join(" ".join(soup.stripped_strings).split())
    normalized = unicodedata.normalize("NFC", text)
    findings, matches = [], 0
    for term, alternative, reason in TERMS:
        pattern = re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", re.I)
        for match in list(pattern.finditer(normalized))[:4]:
            matches += 1
            excerpt = normalized[max(0, match.start()-65):min(len(normalized), match.end()+65)]
            findings.append({"id": f"LANG-REVIEW-{matches}", "rule_id": "LANG-REVIEW", "category": "language",
                "title": f"Revisar expresión: «{term}»", "severity": "review",
                "description": f"Esta expresión puede excluir según el contexto: {reason}", "evidence": excerpt,
                "selector": None, "recommendation": f"Considera «{alternative}» si conserva el significado en este contexto.", "verification": "possible"})
    return findings, [{"id": "LANG-REVIEW", "status": "review", "evidence": f"Se revisaron {len(normalized)} caracteres y se encontraron {matches} coincidencias de reglas; la intención requiere revisión humana."}]
