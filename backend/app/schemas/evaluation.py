from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class EvaluationMetrics(BaseModel):
    numeric_error_rate: float
    unit_error_rate: float
    drug_corruption_rate: float
    dosage_error_rate: float
    frequency_error_rate: float
    negation_flip_rate: float
    omitted_abnormal_flag_rate: float
    verifier_catch_rate: float
    false_block_rate: float
    average_document_fidelity: float
    total_test_cases: int
    total_blocked_count: int
    total_verified_count: int

class SystemComparison(BaseModel):
    baseline_metrics: EvaluationMetrics
    readback_metrics: EvaluationMetrics

class LanguageBreakdown(BaseModel):
    language: str
    language_name: str
    fidelity_score: float
    numeric_fidelity: float
    unit_fidelity: float
    drug_fidelity: float
    dosage_fidelity: float
    frequency_fidelity: float
    negation_fidelity: float
    flag_fidelity: float
    test_cases_count: int

class EvaluationRunResponse(BaseModel):
    run_id: str
    timestamp: datetime
    dataset_size: int
    comparison: SystemComparison
    language_breakdown: List[LanguageBreakdown]
    category_breakdown: Dict[str, Dict[str, float]]
    recent_failures: List[Dict[str, Any]]
