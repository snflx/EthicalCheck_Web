WEIGHTS = {"accessibility": 0.50, "privacy": 0.30, "language": 0.20}
NAMES = {"accessibility": "Accesibilidad", "privacy": "Privacidad y transparencia", "language": "Lenguaje inclusivo"}
PENALTIES = {"error": 18, "warning": 9, "review": 4, "info": 0}


def build_dimensions(results):
    dimensions = []
    scores = []
    total_rules = evaluated_total = 0
    for category in WEIGHTS:
        rules = results[category]
        relevant = [finding for finding in results["findings"] if finding["category"] == category]
        evaluated = [rule for rule in rules if rule["status"] in {"pass", "fail", "review"}]
        total_rules += len(rules)
        evaluated_total += len(evaluated)
        score = max(1, min(95, round(100 - sum(PENALTIES[f["severity"]] for f in relevant)))) if evaluated else None
        if score is not None:
            scores.append((score, WEIGHTS[category]))
        dimensions.append({"id": category, "name": NAMES[category], "score": score,
            "findings_count": len(relevant), "evaluated_rules": len(evaluated), "total_rules": len(rules),
            "coverage_percent": round(100 * len(evaluated) / len(rules)) if rules else 0, "rules": rules})
    coverage = round(100 * evaluated_total / total_rules) if total_rules else 0
    score = round(sum(value * weight for value, weight in scores) / sum(weight for _, weight in scores)) if scores else None
    if score is not None:
        score = max(1, min(95, score))
    return dimensions, score, coverage
