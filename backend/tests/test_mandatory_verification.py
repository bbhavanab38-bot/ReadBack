import pytest
from app.schemas.facts import MedicalFact, FactCategory, FlagType
from app.schemas.verification import VerificationStatus
from app.services.verification.engine import VerificationEngine
from app.services.extraction.independent_extractor import IndependentExtractor
from app.services.navigation.care_navigator import CareNavigator

def test_mandatory_1_exact_match():
    """
    Test 1:
    Original: Hemoglobin = 10.2 g/dL
    Explanation: Hemoglobin = 10.2 g/dL
    Expected: VERIFIED
    """
    orig = [
        MedicalFact(
            field_id="lab_001",
            category=FactCategory.LABORATORY,
            name="Hemoglobin",
            value=10.2,
            unit="g/dL",
            flag=FlagType.LOW,
            source_text="Hemoglobin = 10.2 g/dL",
            confidence=0.98
        )
    ]
    expl_text = "Your blood test indicates your Hemoglobin is 10.2 g/dL, which is LOW."
    extracted_expl_facts = IndependentExtractor.extract_from_explanation(expl_text, orig)
    result = VerificationEngine.verify(orig, extracted_expl_facts)
    assert result.overall_status == VerificationStatus.VERIFIED
    assert result.critical_mismatches_count == 0
    assert result.fidelity_score == 100.0

def test_mandatory_2_numeric_mismatch():
    """
    Test 2:
    Original: Hemoglobin = 10.2 g/dL
    Explanation: Hemoglobin = 12.2 g/dL
    Expected: BLOCKED
    """
    orig = [
        MedicalFact(
            field_id="lab_001",
            category=FactCategory.LABORATORY,
            name="Hemoglobin",
            value=10.2,
            unit="g/dL",
            flag=FlagType.LOW,
            source_text="Hemoglobin = 10.2 g/dL",
            confidence=0.98
        )
    ]
    expl_text = "Your blood test indicates your Hemoglobin is 12.2 g/dL, which is LOW."
    extracted_expl_facts = IndependentExtractor.extract_from_explanation(expl_text, orig)
    result = VerificationEngine.verify(orig, extracted_expl_facts)
    assert result.overall_status == VerificationStatus.BLOCKED
    assert result.critical_mismatches_count >= 1
    assert not result.explanation_safe_to_display
    assert any("Numeric mismatch" in comp.details for comp in result.field_comparisons)

def test_mandatory_3_drug_mismatch():
    """
    Test 3:
    Original: Metformin 500 mg twice daily
    Explanation: Metoprolol 500 mg twice daily
    Expected: BLOCKED
    """
    orig = [
        MedicalFact(
            field_id="med_001",
            category=FactCategory.MEDICATION,
            name="Metformin",
            dosage="500 mg",
            frequency="twice daily",
            source_text="Metformin 500 mg twice daily",
            confidence=0.96
        )
    ]
    expl_text = "Your doctor prescribed Metoprolol 500 mg twice daily for your health."
    extracted_expl_facts = IndependentExtractor.extract_from_explanation(expl_text, orig)
    result = VerificationEngine.verify(orig, extracted_expl_facts)
    assert result.overall_status == VerificationStatus.BLOCKED
    assert result.critical_mismatches_count >= 1
    assert any("CRITICAL DRUG NAME MISMATCH" in comp.details for comp in result.field_comparisons)

def test_mandatory_4_negation_flip():
    """
    Test 4:
    Original: Do not take on an empty stomach.
    Explanation: Take on an empty stomach.
    Expected: BLOCKED
    """
    orig = [
        MedicalFact(
            field_id="inst_001",
            category=FactCategory.INSTRUCTION,
            name="Medication Instruction",
            action="take medication",
            negation=True,
            condition="empty stomach",
            source_text="Do not take on an empty stomach.",
            confidence=0.98
        )
    ]
    expl_text = "Regarding your medication: Please take on an empty stomach with water."
    extracted_expl_facts = IndependentExtractor.extract_from_explanation(expl_text, orig)
    result = VerificationEngine.verify(orig, extracted_expl_facts)
    assert result.overall_status == VerificationStatus.BLOCKED
    assert result.critical_mismatches_count >= 1
    assert any("CRITICAL NEGATION FLIP" in comp.details for comp in result.field_comparisons)

def test_mandatory_5_abnormal_flag_flip():
    """
    Test 5:
    Original: Result: LOW
    Explanation: Result: NORMAL
    Expected: BLOCKED
    """
    orig = [
        MedicalFact(
            field_id="lab_001",
            category=FactCategory.LABORATORY,
            name="Hemoglobin",
            value=10.2,
            unit="g/dL",
            flag=FlagType.LOW,
            source_text="Hemoglobin 10.2 g/dL LOW",
            confidence=0.98
        )
    ]
    expl_text = "Your report shows Hemoglobin is 10.2 g/dL, which is NORMAL."
    extracted_expl_facts = IndependentExtractor.extract_from_explanation(expl_text, orig)
    result = VerificationEngine.verify(orig, extracted_expl_facts)
    assert result.overall_status == VerificationStatus.BLOCKED
    assert result.critical_mismatches_count >= 1
    assert any("Flag mismatch" in comp.details for comp in result.field_comparisons)

@pytest.mark.parametrize(
    ("explanation_text", "mismatch_type"),
    [
        ("Metformin 1000 mg twice daily for 30 days.", "CRITICAL_DOSAGE_MISMATCH"),
        ("Metformin 500 mcg twice daily for 30 days.", "CRITICAL_DOSAGE_MISMATCH"),
        ("Metformin 500 mg once daily for 30 days.", "CRITICAL_FREQUENCY_MISMATCH"),
    ],
)
def test_mandatory_medication_dose_and_frequency_changes_block(explanation_text, mismatch_type):
    original_facts = [
        MedicalFact(
            field_id="med_001",
            category=FactCategory.MEDICATION,
            name="Metformin",
            dosage="500 mg",
            frequency="twice daily",
            duration="30 days",
            source_text="Metformin 500 mg twice daily for 30 days",
            confidence=0.98,
        )
    ]

    explanation_facts = IndependentExtractor.extract_from_explanation(explanation_text, original_facts)
    result = VerificationEngine.verify(original_facts, explanation_facts)

    assert result.overall_status == VerificationStatus.BLOCKED
    assert any(comp.mismatch_type == mismatch_type for comp in result.field_comparisons)

@pytest.mark.parametrize(
    ("explanation_text", "mismatch_type"),
    [
        ("Metformin 500 mg topical twice daily for 30 days.", "CRITICAL_ROUTE_MISMATCH"),
        ("Metformin 500 mg oral twice daily for 14 days.", "CRITICAL_DURATION_MISMATCH"),
    ],
)
def test_mandatory_medication_route_and_duration_changes_block(explanation_text, mismatch_type):
    original_facts = [
        MedicalFact(
            field_id="med_001",
            category=FactCategory.MEDICATION,
            name="Metformin",
            dosage="500 mg",
            frequency="twice daily",
            route="oral",
            duration="30 days",
            source_text="Metformin 500 mg oral twice daily for 30 days",
            confidence=0.98,
        )
    ]

    explanation_facts = IndependentExtractor.extract_from_explanation(explanation_text, original_facts)
    result = VerificationEngine.verify(original_facts, explanation_facts)

    assert result.overall_status == VerificationStatus.BLOCKED
    assert any(comp.mismatch_type == mismatch_type for comp in result.field_comparisons)

def test_missing_critical_lab_value_and_flag_block():
    original_facts = [
        MedicalFact(
            field_id="lab_001",
            category=FactCategory.LABORATORY,
            name="Hemoglobin",
            value=10.2,
            unit="g/dL",
            flag=FlagType.LOW,
            source_text="Hemoglobin 10.2 g/dL LOW",
            confidence=0.98,
        )
    ]

    for explanation_text in (
        "Your hemoglobin result is flagged LOW.",
        "Your hemoglobin is 10.2 g/dL.",
    ):
        explanation_facts = IndependentExtractor.extract_from_explanation(explanation_text, original_facts)
        result = VerificationEngine.verify(original_facts, explanation_facts)
        assert result.overall_status == VerificationStatus.BLOCKED

def test_omitted_normal_lab_field_blocks():
    original_facts = [
        MedicalFact(
            field_id="lab_001",
            category=FactCategory.LABORATORY,
            name="WBC",
            value=7800,
            unit="cells/µL",
            flag=FlagType.NORMAL,
            source_text="WBC 7800 cells/µL NORMAL",
            confidence=0.98,
        )
    ]

    result = VerificationEngine.verify(original_facts, [])

    assert result.overall_status == VerificationStatus.BLOCKED

def test_lab_unit_change_blocks_even_when_number_matches():
    original_facts = [
        MedicalFact(
            field_id="lab_001",
            category=FactCategory.LABORATORY,
            name="Hemoglobin",
            value=10.2,
            unit="g/dL",
            flag=FlagType.LOW,
            source_text="Hemoglobin 10.2 g/dL LOW",
            confidence=0.98,
        )
    ]

    explanation_facts = IndependentExtractor.extract_from_explanation(
        "Your hemoglobin is 10.2 mg/dL, which is LOW.", original_facts
    )
    result = VerificationEngine.verify(original_facts, explanation_facts)

    assert result.overall_status == VerificationStatus.BLOCKED
    assert any(comp.mismatch_type == "UNIT_MISMATCH" for comp in result.field_comparisons)

def test_verified_next_step_does_not_invent_specialty():
    next_step = CareNavigator.extract_verified_next_step("Follow-up consultation after 2 weeks.")

    assert next_step.has_next_step is True
    assert next_step.source_text == "Follow-up consultation after 2 weeks."
    assert next_step.timing == "2 weeks"
    assert next_step.department_or_specialty is None

def test_mandatory_6_verified_next_step():
    """
    Test 6 — Verified Next Step:
    Original: Follow-up consultation after 2 weeks.
    Expected: Service: Follow-up consultation, Timing: 2 weeks, Status: VERIFIED
    """
    doc_text = (
        "Hemoglobin: 10.2 g/dL\n"
        "Follow-up consultation after 2 weeks."
    )
    next_step = CareNavigator.extract_verified_next_step(doc_text)
    assert next_step.has_next_step is True
    assert next_step.service_name == "Follow-up consultation"
    assert "2 weeks" in next_step.timing
    assert next_step.verification_status == "VERIFIED"

def test_mandatory_7_no_unsupported_navigation():
    """
    Test 7 — No Unsupported Navigation:
    Original: Hemoglobin: 10.2 g/dL
    Expected: No verified healthcare-service instruction found.
    System must NOT invent 'See a hematologist.'
    """
    doc_text = "Hemoglobin: 10.2 g/dL"
    next_step = CareNavigator.extract_verified_next_step(doc_text)
    assert next_step.has_next_step is False
    assert next_step.service_name is None
    assert next_step.verification_status == "NO_EXPLICIT_INSTRUCTION"
    assert "No explicit healthcare-service" in next_step.rationale
