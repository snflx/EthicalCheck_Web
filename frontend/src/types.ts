export type Finding = {
  id: string; rule_id: string; category: 'accessibility' | 'privacy' | 'language'; title: string;
  severity: 'error' | 'warning' | 'review' | 'info'; description: string; evidence: string;
  selector: string | null; recommendation: string;
  verification: 'confirmed' | 'possible' | 'not_evaluated' | 'not_applicable';
}
export type RuleResult = { id: string; status: 'pass' | 'fail' | 'review' | 'not_evaluated' | 'not_applicable'; evidence: string }
export type Dimension = { id: string; name: string; score: number | null; findings_count: number; evaluated_rules: number; total_rules: number; coverage_percent: number; rules: RuleResult[] }
export type Report = { engine_version: string; analyzed_url: string; analyzed_at: string; status: 'completed' | 'partial'; score: number | null; score_label: string; coverage_percent: number; dimensions: Dimension[]; findings: Finding[]; limitations: string[] }
