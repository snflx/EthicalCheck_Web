import re
from urllib.parse import urljoin, urlsplit


def analyze_privacy(soup, url):
    findings, rules = [], []
    text = " ".join(soup.stripped_strings)
    links = [(" ".join(a.stripped_strings).lower(), a.get("href", "")) for a in soup.find_all("a", href=True)]
    patterns = {
        "PRIVACY-POLICY": (r"privacidad|privacy|datos personales|protecci[oó]n de datos", "Política de privacidad", "Haz accesible una política que explique qué datos se recogen, para qué y cómo ejercer derechos."),
        "PRIVACY-TERMS": (r"t[eé]rminos|condiciones de uso|terms of service", "Condiciones de uso", "Publica las condiciones de uso aplicables al servicio."),
        "PRIVACY-COOKIES": (r"cookies|preferencias de privacidad|gesti[oó]n de cookies", "Información sobre cookies", "Explica las cookies utilizadas y cómo gestionar las preferencias."),
        "PRIVACY-CONTACT": (r"contacto|contact us|responsable del tratamiento", "Contacto o responsable identificable", "Indica un medio de contacto o la identidad del responsable cuando corresponda."),
    }
    for rule, (pattern, title, recommendation) in patterns.items():
        matches = [(label, href) for label, href in links if re.search(pattern, label + " " + href, re.I)]
        found = bool(matches) or bool(re.search(pattern, text, re.I))
        rules.append({"id": rule, "status": "pass" if found else "fail",
                      "evidence": f"Se detectó una referencia: {matches[0][1] if matches else 'texto visible'}" if found else "No se detectó una referencia visible."})
        if not found:
            findings.append({"id": f"{rule}-1", "rule_id": rule, "category": "privacy", "title": f"No se detectó {title.lower()}",
                "severity": "review", "description": "La búsqueda automática no encontró una referencia visible; esto no demuestra una infracción ni descarta contenido en otras rutas.",
                "evidence": "No se encontró texto o enlace coincidente en la página analizada.", "selector": None,
                "recommendation": recommendation, "verification": "possible"})

    forms = soup.find_all("form")
    sensitive_fields = []
    for form in forms:
        for field in form.find_all(["input", "select", "textarea"]):
            descriptor = " ".join(str(field.get(key, "")) for key in ("type", "name", "id", "autocomplete", "placeholder")).lower()
            if re.search(r"email|correo|tel|phone|nombre|name|address|direcci[oó]n|document|identificaci[oó]n|passport|password|contrase[nñ]a", descriptor):
                sensitive_fields.append((form, field))
    rules.append({"id": "PRIVACY-PERSONAL-FORM", "status": "review" if sensitive_fields else "pass",
                 "evidence": f"Se detectaron {len(sensitive_fields)} campos que podrían solicitar datos personales en {len(forms)} formularios."})
    for form, field in sensitive_fields[:20]:
        findings.append({"id": f"PRIVACY-PERSONAL-FORM-{len(findings)+1}", "rule_id": "PRIVACY-PERSONAL-FORM", "category": "privacy",
            "title": "Campo que podría solicitar datos personales", "severity": "review", "description": "La página contiene un campo cuyo nombre sugiere datos personales; no se envió información ni se comprobó su propósito.",
            "evidence": f"<{field.name} type='{field.get('type', '')}' name='{field.get('name', '')}'>", "selector": "form", "recommendation": "Solicita solo los datos necesarios y explica el propósito y tratamiento antes del envío.", "verification": "possible"})

    insecure = []
    for form in forms:
        target = urlsplit(urljoin(url, form.get("action") or url))
        if target.scheme.lower() == "http" and (form.get("method", "get").lower() == "post" or any(pair[0] is form for pair in sensitive_fields)):
            insecure.append(form)
    rules.append({"id": "PRIVACY-FORM-HTTPS", "status": "fail" if insecure else "pass",
                 "evidence": f"{len(insecure)} formularios podrían enviar datos mediante HTTP; {len(forms)} formularios revisados."})
    for form in insecure[:20]:
        findings.append({"id": f"PRIVACY-FORM-HTTPS-{len(findings)+1}", "rule_id": "PRIVACY-FORM-HTTPS", "category": "privacy",
            "title": "Formulario con destino HTTP", "severity": "error", "description": "El formulario parece enviar datos en texto claro por HTTP.",
            "evidence": f"action={form.get('action', '(misma página)')}", "selector": "form", "recommendation": "Sirve la página y el endpoint del formulario exclusivamente por HTTPS.", "verification": "confirmed"})
    https = url.startswith("https://")
    rules.append({"id": "PRIVACY-HTTPS", "status": "pass" if https else "fail", "evidence": "La página usa HTTPS." if https else "La página usa HTTP sin cifrado de transporte."})
    if not https:
        findings.append({"id": "PRIVACY-HTTPS-1", "rule_id": "PRIVACY-HTTPS", "category": "privacy", "title": "La página no usa HTTPS", "severity": "warning",
            "description": "La conexión inicial no cifra el transporte.", "evidence": url, "selector": None,
            "recommendation": "Configura HTTPS y redirige el tráfico HTTP de forma segura.", "verification": "confirmed"})
    consent_pattern = r"aceptar (?:todas )?las cookies|consentimiento de cookies|gestionar (?:mis )?preferencias|rechazar cookies"
    consent_found = bool(re.search(consent_pattern, text, re.I))
    rules.append({"id": "PRIVACY-CONSENT", "status": "review" if consent_found else "not_evaluated",
        "evidence": "Se detectó texto que parece corresponder a un aviso de consentimiento; no se validó su funcionamiento." if consent_found else "No se detectó un aviso de consentimiento visible. No se interactuó con mecanismos dinámicos."})
    if consent_found:
        findings.append({"id": "PRIVACY-CONSENT-1", "rule_id": "PRIVACY-CONSENT", "category": "privacy", "title": "Posible aviso de consentimiento visible", "severity": "info",
            "description": "Se encontró texto asociado a cookies; la detección no determina si el aviso es válido ni si respeta preferencias.", "evidence": re.search(consent_pattern, text, re.I).group(0), "selector": None,
            "recommendation": "Revisa manualmente que las opciones sean claras, accesibles y respeten la elección de la persona.", "verification": "possible"})
    return findings, rules
