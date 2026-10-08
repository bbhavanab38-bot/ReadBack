import pytest
from fastapi.testclient import TestClient

from app.main import app

from app.schemas.facts import FactCategory, FlagType, MedicalFact
from app.schemas.fidelity import FidelityFailureType
from app.schemas.verification import VerificationStatus
from app.services.fidelity_lab import FidelitySimulationError, simulate_ai_error

client = TestClient(app)


@pytest.mark.parametrize(
    ("failure_type", "facts", "explanation", "field_name"),
    [
        (
            FidelityFailureType.NUMERIC_VALUE_CHANGED,
            [MedicalFact(field_id="lab_1", category=FactCategory.LABORATORY, name="Hemoglobin", value=10.2, unit="g/dL", flag=FlagType.LOW, source_text="Hemoglobin 10.2 g/dL LOW", confidence=0.98)],
            "Your report shows a Hemoglobin level of 10.2 g/dL, flagged as LOW.",
            "Hemoglobin",
        ),
        (
            FidelityFailureType.UNIT_CHANGED,
            [MedicalFact(field_id="lab_1", category=FactCategory.LABORATORY, name="Hemoglobin", value=10.2, unit="g/dL", flag=FlagType.LOW, source_text="Hemoglobin 10.2 g/dL LOW", confidence=0.98)],
            "Your report shows a Hemoglobin level of 10.2 g/dL, flagged as LOW.",
            "Hemoglobin",
        ),
        (
            FidelityFailureType.ABNORMAL_FLAG_CHANGED,
            [MedicalFact(field_id="lab_1", category=FactCategory.LABORATORY, name="Hemoglobin", value=10.2, unit="g/dL", flag=FlagType.LOW, source_text="Hemoglobin 10.2 g/dL LOW", confidence=0.98)],
            "Your report shows a Hemoglobin level of 10.2 g/dL, flagged as LOW.",
            "Hemoglobin",
        ),
        (
            FidelityFailureType.DRUG_NAME_CHANGED,
            [MedicalFact(field_id="med_1", category=FactCategory.MEDICATION, name="Metformin", dosage="500 mg", frequency="twice daily", source_text="Metformin 500 mg twice daily", confidence=0.98)],
            "Prescribed medication: Metformin 500 mg, to be taken twice daily.",
            "Metformin",
        ),
        (
            FidelityFailureType.DOSAGE_CHANGED,
            [MedicalFact(field_id="med_1", category=FactCategory.MEDICATION, name="Metformin", dosage="500 mg", frequency="twice daily", source_text="Metformin 500 mg twice daily", confidence=0.98)],
            "Prescribed medication: Metformin 500 mg, to be taken twice daily.",
            "Metformin",
        ),
        (
            FidelityFailureType.FREQUENCY_CHANGED,
            [MedicalFact(field_id="med_1", category=FactCategory.MEDICATION, name="Metformin", dosage="500 mg", frequency="twice daily", source_text="Metformin 500 mg twice daily", confidence=0.98)],
            "Prescribed medication: Metformin 500 mg, to be taken twice daily.",
            "Metformin",
        ),
        (
            FidelityFailureType.NEGATION_FLIPPED,
            [MedicalFact(field_id="inst_1", category=FactCategory.INSTRUCTION, name="Medication Instruction", action="take medication", negation=True, condition="empty stomach", instruction_text="Do not take on an empty stomach.", source_text="Do not take on an empty stomach.", confidence=0.98)],
            "Important instruction: Do NOT take medication on/with empty stomach.",
            "Medication Instruction",
        ),
        (
            FidelityFailureType.IMPORTANT_FACT_OMITTED,
            [MedicalFact(field_id="lab_1", category=FactCategory.LABORATORY, name="Hemoglobin", value=10.2, unit="g/dL", flag=FlagType.LOW, source_text="Hemoglobin 10.2 g/dL LOW", confidence=0.98)],
            "Your report shows a Hemoglobin level of 10.2 g/dL, flagged as LOW.",
            "Hemoglobin",
        ),
    ],
)
def test_failure_simulation_uses_verifier_and_preserves_original_facts(failure_type, facts, explanation, field_name):
    original_snapshot = [fact.model_dump() for fact in facts]

    simulation = simulate_ai_error("doc-1", explanation, facts, failure_type)

    assert simulation.demo_label == "DEMO: INTENTIONALLY CORRUPTED AI OUTPUT"
    assert simulation.verification_result.overall_status == VerificationStatus.BLOCKED
    assert simulation.verification_result.explanation_safe_to_display is False
    assert simulation.original_explanation == explanation
    if failure_type == FidelityFailureType.DRUG_NAME_CHANGED:
        assert "Metoprolol" in simulation.simulated_explanation
        assert "Metformin" not in simulation.simulated_explanation
    elif failure_type == FidelityFailureType.NEGATION_FLIPPED:
        assert "Do NOT" not in simulation.simulated_explanation
    elif failure_type == FidelityFailureType.IMPORTANT_FACT_OMITTED:
        assert field_name not in simulation.simulated_explanation
    else:
        assert field_name in simulation.simulated_explanation
    assert [fact.model_dump() for fact in facts] == original_snapshot
    assert any(comparison.status == "MISMATCH" for comparison in simulation.verification_result.field_comparisons)


def test_simulation_refuses_unverified_baseline():
    facts = [MedicalFact(field_id="lab_1", category=FactCategory.LABORATORY, name="Hemoglobin", value=10.2, unit="g/dL", flag=FlagType.LOW, source_text="Hemoglobin 10.2 g/dL LOW", confidence=0.98)]

    with pytest.raises(FidelitySimulationError, match="passes current ReadBack verification"):
        simulate_ai_error("doc-1", "Your report shows Hemoglobin is 12.2 mg/dL NORMAL.", facts, FidelityFailureType.NUMERIC_VALUE_CHANGED)


def test_fidelity_lab_demo_api_uses_real_fixture_and_simulation_does_not_mutate_document():
    uploaded = client.post("/documents/upload", data={"demo_type": "fidelity_lab_cbc"})
    assert uploaded.status_code == 200
    original = uploaded.json()
    document_id = original["id"]

    explained = client.post(f"/documents/{document_id}/explain", json={"language": "en"})
    assert explained.status_code == 200
    verified = client.post(f"/documents/{document_id}/verify")
    assert verified.status_code == 200
    if verified.json()["overall_status"] != "VERIFIED":
        pytest.fail(f"Checked-in fidelity demo fixture did not verify: {verified.json()}")

    before = client.get(f"/documents/{document_id}").json()
    simulated = client.post(
        f"/documents/{document_id}/simulate-ai-error",
        json={"failure_type": "numeric_value_changed"},
    )
    assert simulated.status_code == 200
    result = simulated.json()
    assert result["demo_label"] == "DEMO: INTENTIONALLY CORRUPTED AI OUTPUT"
    assert result["verification_result"]["overall_status"] == "BLOCKED"

    after = client.get(f"/documents/{document_id}").json()
    assert after["extracted_facts"] == before["extracted_facts"]
    assert after["confirmed_facts"] == before["confirmed_facts"]
    assert after["explanation_text"] == before["explanation_text"]
    assert after["verification_result"] == before["verification_result"]


def test_fidelity_lab_prescription_negation_simulation_is_blocked_without_mutation():
    uploaded = client.post("/documents/upload", data={"demo_type": "fidelity_lab_prescription"})
    assert uploaded.status_code == 200
    document_id = uploaded.json()["id"]

    explained = client.post(f"/documents/{document_id}/explain", json={"language": "en"})
    assert explained.status_code == 200
    verified = client.post(f"/documents/{document_id}/verify")
    assert verified.json()["overall_status"] == "VERIFIED"
    before = client.get(f"/documents/{document_id}").json()

    simulated = client.post(
        f"/documents/{document_id}/simulate-ai-error",
        json={"failure_type": "negation_flipped"},
    )

    assert simulated.status_code == 200
    response = simulated.json()
    assert response["verification_result"]["overall_status"] == "BLOCKED"
    assert any(
        comparison["mismatch_type"] == "CRITICAL_NEGATION_FLIP"
        for comparison in response["verification_result"]["field_comparisons"]
    )
    after = client.get(f"/documents/{document_id}").json()
    assert after["confirmed_facts"] == before["confirmed_facts"]
    assert after["explanation_text"] == before["explanation_text"]
    assert after["verification_result"] == before["verification_result"]