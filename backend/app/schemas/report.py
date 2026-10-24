from typing import Literal
from pydantic import BaseModel, HttpUrl


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class Finding(BaseModel):
    id: str
    rule_id: str
    category: Literal["accessibility", "privacy", "language"]
    title: str
    severity: Literal["error", "warning", "review", "info"]
    description: str
    evidence: str
    selector: str | None = None
    recommendation: str
    verification: Literal["confirmed", "possible", "not_evaluated", "not_applicable"]


class RuleResult(BaseModel):
    id: str
    status: Literal["pass", "fail", "review", "not_evaluated", "not_applicable"]
    evidence: str


class Dimension(BaseModel):
    id: str
    name: str
    score: int | None
    findings_count: int
    evaluated_rules: int
    total_rules: int
    coverage_percent: int
    rules: list[RuleResult]


class Report(BaseModel):
    engine_version: str
    analyzed_url: str
    analyzed_at: str
    status: Literal["completed", "partial"]
    score: int | None
    score_label: str
    coverage_percent: int
    dimensions: list[Dimension]
    findings: list[Finding]
    limitations: list[str]
