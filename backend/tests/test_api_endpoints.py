import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "en" in data["supported_languages"]


def test_unreadable_and_corrupt_real_uploads_return_clear_errors():
    from io import BytesIO
    from PIL import Image

    blank = BytesIO()
    Image.new("RGB", (400, 200), "white").save(blank, format="PNG")
    blank_response = client.post(
        "/documents/upload",
        files={"file": ("blank.png", blank.getvalue(), "image/png")},
    )
    assert blank_response.status_code == 422
    assert "no readable text" in blank_response.json()["detail"].lower()

    corrupt_response = client.post(
        "/documents/upload",
        files={"file": ("corrupt.pdf", b"not a PDF", "application/pdf")},
    )
    assert corrupt_response.status_code == 422
    assert "pdf extraction failed" in corrupt_response.json()["detail"].lower()


def test_missing_ocr_engines_return_a_specific_error():
    from unittest.mock import patch
    from app.services.ocr.ocr_service import OCRUnavailableError

    with patch("app.api.documents.extract_document_text", side_effect=OCRUnavailableError):
        response = client.post(
            "/documents/upload",
            files={"file": ("scan.pdf", b"valid upload body", "application/pdf")},
        )

    assert response.status_code == 503
    assert "no OCR engine is available" in response.json()["detail"]


def test_upload_without_file_requires_explicit_demo_selection():
    response = client.post("/documents/upload")

    assert response.status_code == 422
    assert "explicit demo selection" in response.json()["detail"].lower()


def test_synthetic_cbc_upload_continues_through_readback_pipeline():
    from pathlib import Path

    report_path = Path(__file__).parents[1] / "uploads" / "a4609810-5174-4b62-8561-c71d0d7eeb3f_DEMO_CBC_Blood_Report.txt"
    report_text = report_path.read_text(encoding="utf-8")
    report_text += "\nDo not take the prescribed medicine on an empty stomach."
    uploaded = client.post(
        "/documents/upload",
        files={"file": ("synthetic-cbc.txt", report_text, "text/plain")},
    )
    assert uploaded.status_code == 200
    document = uploaded.json()
    hemoglobin = next(fact for fact in document["extracted_facts"] if fact["name"] == "Hemoglobin")
    assert hemoglobin["value"] == 10.2
    assert hemoglobin["unit"] == "g/dL"
    assert hemoglobin["reference_range"] == "12.0-16.0"
    assert hemoglobin["flag"] == "LOW"
    assert any("Do not take on an empty stomach" in fact["source_text"] for fact in document["extracted_facts"])
    assert any(
        fact["instruction_text"] == "Do not take the prescribed medicine on an empty stomach."
        for fact in document["extracted_facts"]
    )

    explanation = client.post(f"/documents/{document['id']}/explain", json={"language": "en"})
    assert explanation.status_code == 200
    assert any("Hemoglobin" in line for line in explanation.json()["summary_bullet_points"])
    verification = client.post(f"/documents/{document['id']}/verify")
    assert verification.status_code == 200
    assert "overall_status" in verification.json()
    next_step = client.get(f"/documents/{document['id']}/next-step")
    assert next_step.status_code == 200
    assert next_step.json()["has_next_step"] is True
    assert "2 weeks" in next_step.json()["timing"]

def test_demo_upload_and_pipeline():
    # 1. Upload demo document
    res_upload = client.post("/documents/upload", data={"demo_type": "lab_report"})
    assert res_upload.status_code == 200
    doc = res_upload.json()
    doc_id = doc["id"]
    assert doc_id is not None
    assert len(doc["extracted_facts"]) >= 1

    # 2. Confirm facts
    res_confirm = client.post(f"/documents/{doc_id}/confirm", json={
        "confirmed_facts": doc["extracted_facts"]
    })
    assert res_confirm.status_code == 200

    # 3. Explain document
    res_explain = client.post(f"/documents/{doc_id}/explain", json={
        "language": "en"
    })
    assert res_explain.status_code == 200
    expl = res_explain.json()
    assert expl["explanation_text"] == ""

    # 4. Verify document explanation
    res_verify = client.post(f"/documents/{doc_id}/verify")
    assert res_verify.status_code == 200
    verification = res_verify.json()
    assert verification["overall_status"] == "VERIFIED"
    assert verification["fidelity_score"] >= 90.0
    verified_doc = client.get(f"/documents/{doc_id}").json()
    assert verified_doc["explanation_text"]
    assert verified_doc["explanation_pending_verification"] is False

    # 5. Check Next Step
    res_ns = client.get(f"/documents/{doc_id}/next-step")
    assert res_ns.status_code == 200
    ns = res_ns.json()
    assert ns["has_next_step"] is True
    assert "Follow-up consultation" in ns["service_name"]

def test_demo_blocked_numeric_hallucination():
    # Upload and intentionally corrupt explanation with numeric mismatch
    res_upload = client.post("/documents/upload", data={"demo_type": "lab_report"})
    assert res_upload.status_code == 200
    doc = res_upload.json()
    doc_id = doc["id"]

    # Explain with deliberate number corruption
    res_explain = client.post(f"/documents/{doc_id}/explain", json={
        "language": "en",
        "corrupt_for_testing": "number"
    })
    assert res_explain.status_code == 200

    # Verify -> Must BLOCK
    res_verify = client.post(f"/documents/{doc_id}/verify")
    assert res_verify.status_code == 200
    ver = res_verify.json()
    assert ver["overall_status"] == "BLOCKED"
    assert ver["critical_mismatches_count"] >= 1
    assert ver["explanation_safe_to_display"] is False

def test_prescription_pipeline_verifies_each_medication_independently():
    uploaded = client.post("/documents/upload", data={"demo_type": "prescription"})
    assert uploaded.status_code == 200
    doc_id = uploaded.json()["id"]

    explained = client.post(f"/documents/{doc_id}/explain", json={"language": "en"})
    assert explained.status_code == 200

    verified = client.post(f"/documents/{doc_id}/verify")
    assert verified.status_code == 200
    result = verified.json()
    assert result["overall_status"] == "VERIFIED"
    assert result["critical_mismatches_count"] == 0

def test_unverified_and_blocked_explanations_are_not_exposed_by_document_api():
    uploaded = client.post("/documents/upload", data={"demo_type": "lab_report"})
    doc_id = uploaded.json()["id"]

    explained = client.post(f"/documents/{doc_id}/explain", json={
        "language": "en",
        "corrupt_for_testing": "number",
    })
    assert explained.status_code == 200
    assert explained.json()["explanation_text"] == ""

    pending = client.get(f"/documents/{doc_id}").json()
    assert pending["explanation_text"] is None
    assert pending["explanation_pending_verification"] is True

    verified = client.post(f"/documents/{doc_id}/verify")
    assert verified.json()["overall_status"] == "BLOCKED"

    blocked = client.get(f"/documents/{doc_id}").json()
    assert blocked["explanation_text"] is None
    assert blocked["explanation_pending_verification"] is False

def test_multilingual_kannada_explanation():
    res_upload = client.post("/documents/upload", data={"demo_type": "lab_report"})
    doc_id = res_upload.json()["id"]

    res_explain = client.post(f"/documents/{doc_id}/explain", json={
        "language": "kn"
    })
    assert res_explain.status_code == 200
    assert "ಹಿಮೋಗ್ಲೋಬಿನ್" in res_explain.json()["explanation_text"]

def test_document_comparison_conflict_detection():
    # Upload doc A (prescription with Metformin 500 mg)
    res_a = client.post("/documents/upload", data={"demo_type": "prescription"})
    doc_a_id = res_a.json()["id"]

    # Upload doc B and modify fact to Metformin 250 mg to simulate dosage conflict
    res_b = client.post("/documents/upload", data={"demo_type": "prescription"})
    doc_b_id = res_b.json()["id"]
    facts_b = res_b.json()["extracted_facts"]
    for f in facts_b:
        if f["name"] == "Metformin":
            f["dosage"] = "250 mg"
            f["strength"] = "250 mg"
    client.post(f"/documents/{doc_b_id}/confirm", json={"confirmed_facts": facts_b})

    res_comp = client.post("/documents/compare", json=[doc_a_id, doc_b_id])
    assert res_comp.status_code == 200
    comp_data = res_comp.json()
    assert comp_data["has_conflicts"] is True
    assert any(("500 mg" in c["warning_message"] and "250 mg" in c["warning_message"]) for c in comp_data["conflicts"])
