from bs4 import BeautifulSoup


def _selector(tag):
    name = tag.name or "elemento"
    if tag.get("id"):
        return f"{name}#{tag['id'][:80]}"
    classes = "".join(f".{c}" for c in tag.get("class", [])[:2])
    return f"{name}{classes}"[:100]


def analyze_accessibility(soup: BeautifulSoup):
    findings, rules = [], []

    def add(rule, title, severity, description, evidence, recommendation, selector=None, verification="confirmed"):
        findings.append({"id": f"{rule}-{len(findings)+1}", "rule_id": rule,
            "category": "accessibility", "title": title, "severity": severity,
            "description": description, "evidence": evidence[:240], "selector": selector,
            "recommendation": recommendation, "verification": verification})

    images = soup.find_all("img")
    missing = [img for img in images if not img.has_attr("alt")]
    rules.append({"id": "A11Y-IMG-ALT", "status": "fail" if missing else "pass",
                  "evidence": f"{len(missing)} de {len(images)} imágenes no declaran alt."})
    for img in missing[:20]:
        add("A11Y-IMG-ALT", "Imagen sin atributo alt", "error",
            "La imagen no declara una alternativa textual; no es posible determinar si es informativa o decorativa.",
            str(img.get("src", "(sin src)")), "Añade un alt descriptivo si aporta información o alt='' si es decorativa.", _selector(img), "possible")

    forms = soup.find_all(["input", "select", "textarea"])
    unlabeled = []
    for control in forms:
        if control.get("type") in {"hidden", "submit", "button", "reset"}:
            continue
        labelled = bool(control.get("aria-label") or control.get("aria-labelledby") or control.find_parent("label"))
        if control.get("id") and soup.find("label", attrs={"for": control["id"]}):
            labelled = True
        if not labelled:
            unlabeled.append(control)
    rules.append({"id": "A11Y-FORM-LABEL", "status": "fail" if unlabeled else "pass",
                  "evidence": f"{len(unlabeled)} controles de formulario sin etiqueta asociada."})
    for tag in unlabeled[:20]:
        add("A11Y-FORM-LABEL", "Control sin etiqueta accesible", "error",
            "No se encontró una etiqueta HTML ni un nombre ARIA asociado al control.",
            f"<{tag.name} type='{tag.get('type','')}' name='{tag.get('name','')}'>",
            "Asocia un <label for> al control o proporciona aria-label/aria-labelledby.", _selector(tag))

    unnamed = [tag for tag in soup.find_all(["button", "a"]) if not " ".join(tag.stripped_strings).strip()
               and not tag.get("aria-label") and not tag.get("aria-labelledby") and not tag.find("img", alt=True)]
    rules.append({"id": "A11Y-NAME", "status": "fail" if unnamed else "pass",
                  "evidence": f"{len(unnamed)} botones o enlaces sin nombre accesible detectado."})
    for tag in unnamed[:20]:
        add("A11Y-NAME", "Elemento interactivo sin nombre", "error",
            "El control no tiene texto visible ni un nombre accesible detectable.", str(tag)[:180],
            "Añade texto visible o un nombre accesible que describa su propósito.", _selector(tag))

    lang = bool(soup.html and soup.html.get("lang"))
    rules.append({"id": "A11Y-LANG", "status": "pass" if lang else "fail",
                  "evidence": f"Idioma declarado: {soup.html.get('lang')}" if lang else "El elemento <html> no declara lang."})
    if not lang:
        add("A11Y-LANG", "Idioma del documento no declarado", "warning",
            "Los lectores de pantalla pueden pronunciar el contenido con reglas de idioma incorrectas.", "<html> sin atributo lang",
            "Declara el idioma principal, por ejemplo <html lang='es'>.", "html")

    headings = [int(tag.name[1]) for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])]
    skips = any(curr - prev > 1 for prev, curr in zip(headings, headings[1:]))
    rules.append({"id": "A11Y-HEADING-ORDER", "status": "fail" if skips else "pass",
                  "evidence": "Se detectó un salto de nivel en encabezados." if skips else f"Se inspeccionaron {len(headings)} encabezados."})
    if skips:
        add("A11Y-HEADING-ORDER", "Posible salto en niveles de encabezado", "warning",
            "La secuencia de encabezados omite uno o más niveles.", "Niveles: " + ", ".join(map(str, headings[:20])),
            "Organiza los encabezados jerárquicamente sin saltar niveles.", verification="possible")

    rules.extend([
        {"id": "A11Y-CONTRAST", "status": "not_evaluated", "evidence": "El contraste real requiere estilos computados del navegador."},
        {"id": "A11Y-ARIA", "status": "not_evaluated", "evidence": "La validación completa de ARIA requiere un motor DOM y axe-core."},
        {"id": "A11Y-KEYBOARD", "status": "not_evaluated", "evidence": "No se ejecutaron interacciones de teclado."},
    ])
    return findings, rules
