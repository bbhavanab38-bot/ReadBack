"""
Regression tests for PDF laboratory table parsing, document classification,
and independent re-extraction.

Covers the bugs fixed in the extraction pipeline:
- PDF text extraction emits one table cell per line (PyMuPDF), which used to
  yield zero lab facts from the CBC and Lipid demo PDFs.
- Comma-grouped numbers ("7,800") and ranges ("4,000 - 11,000") failed to parse.
- Inequality reference ranges ("< 200 mg/dL") were unsupported.
- LDL/HDL rows were mislabelled as Total Cholesterol.
- The unit "U/L" was mistaken for a LOW flag on SGPT / ALT.
- Lab PDFs were classified as prescriptions because a disclaimer mentioned
  the word "PRESCRIPTION".
- The verifier's independent extractor did not recognise "mil/µL" (RBC) or
  the LDL/HDL/Triglycerides terms, which blocked verification.
"""
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.facts import FactCategory, FlagType
from app.services.extraction.parser import DocumentFactParser
from app.services.ocr.ocr_service import extract_document_text

client = TestClient(app)

DEMO_DATA_DIR = Path(__file__).parents[2] / "demo-data"
CBC_PDF = DEMO_DATA_DIR / "01_CBC_Blood_Report.pdf"
LIPID_PDF = DEMO_DATA_DIR / "03_Followup_Lipid_Report.pdf"
PRESCRIPTION_PDF = DEMO_DATA_DIR / "02_Prescription_Demo.pdf"


def parse_pdf(path, document_type="lab_report"):
    extraction = extract_document_text(str(path), "paddleocr")
    return DocumentFactParser.parse_document_text(
        extraction.raw_text, document_type=document_type
    )


def labs_by_name(result):
    return {f.name: f for f in result.facts if f.category == FactCategory.LABORATORY}


def test_cbc_pdf_extracts_four_lab_values_and_instruction():
    result = parse_pdf(CBC_PDF)

    labs = labs_by_name(result)
    assert set(labs) == {"Hemoglobin", "WBC", "Platelets", "RBC"}

    hemoglobin = labs["Hemoglobin"]
    assert hemoglobin.value == 10.2
    assert hemoglobin.unit == "g/dL"
    assert hemoglobin.reference_range == "12.0-16.0"
    assert hemoglobin.flag == FlagType.LOW

    wbc = labs["WBC"]
    assert wbc.value == 7800.0
    assert wbc.unit == "cells/µL"
    assert wbc.reference_range == "4000-11000"
    assert wbc.flag == FlagType.NORMAL

    platelets = labs["Platelets"]
    assert platelets.value == 210000.0
    assert platelets.reference_range == "150000-450000"
    assert platelets.flag == FlagType.NORMAL

    rbc = labs["RBC"]
    assert rbc.value == 4.1
    assert rbc.unit == "mil/µL"
    assert rbc.reference_range == "3.8-5.2"
    assert rbc.flag == FlagType.NORMAL

    instructions = [f for f in result.facts if f.category == FactCategory.INSTRUCTION]
    assert len(instructions) == 1
    assert instructions[0].negation is True
    assert "empty stomach" in instructions[0].instruction_text.lower()


def test_lipid_pdf_extracts_four_lipids_with_mg_dl_units():
    result = parse_pdf(LIPID_PDF)

    labs = labs_by_name(result)
    assert set(labs) == {"Total Cholesterol", "LDL Cholesterol", "HDL Cholesterol", "Triglycerides"}

    expected = {
        "Total Cholesterol": (198.0, "<200", FlagType.NORMAL),
        "LDL Cholesterol": (118.0, "<130", FlagType.NORMAL),
        "HDL Cholesterol": (46.0, ">40", FlagType.NORMAL),
        "Triglycerides": (168.0, "<150", FlagType.HIGH),
    }
    for name, (value, ref_range, flag) in expected.items():
        fact = labs[name]
        assert fact.value == value
        assert fact.unit == "mg/dL"
        assert fact.reference_range == ref_range
        assert fact.flag == flag


def test_comma_grouped_numbers_and_ranges_parse():
    result = DocumentFactParser.parse_document_text(
        "WBC Count 7,800 cells/µL 4,000 - 11,000 NORMAL",
        document_type="lab_report",
    )
    wbc = labs_by_name(result)["WBC"]
    assert wbc.value == 7800.0
    assert wbc.unit == "cells/µL"
    assert wbc.reference_range == "4000-11000"
    assert wbc.flag == FlagType.NORMAL


def test_inequality_reference_range_parses():
    result = DocumentFactParser.parse_document_text(
        "Fasting Blood Glucose 110 mg/dL < 100 mg/dL HIGH",
        document_type="lab_report",
    )
    glucose = labs_by_name(result)["Fasting Blood Glucose"]
    assert glucose.value == 110.0
    assert glucose.unit == "mg/dL"
    assert glucose.reference_range == "<100"
    assert glucose.flag == FlagType.HIGH


def test_ldl_and_hdl_are_not_mislabelled_as_total_cholesterol():
    result = DocumentFactParser.parse_document_text(
        "LDL Cholesterol 118 mg/dL < 130 mg/dL\n"
        "HDL Cholesterol 46 mg/dL > 40 mg/dL\n"
        "Total Cholesterol 198 mg/dL < 200 mg/dL",
        document_type="lab_report",
    )
    assert set(labs_by_name(result)) == {
        "LDL Cholesterol",
        "HDL Cholesterol",
        "Total Cholesterol",
    }


def test_unit_slash_l_is_not_read_as_low_flag():
    result = DocumentFactParser.parse_document_text(
        "SGPT / ALT 28 U/L Ref: (7 - 56) NORMAL",
        document_type="lab_report",
    )
    sgpt = labs_by_name(result)["SGPT / ALT"]
    assert sgpt.value == 28.0
    assert sgpt.unit == "U/L"
    assert sgpt.flag == FlagType.NORMAL


def upload_pdf(path):
    with path.open("rb") as pdf:
        response = client.post(
            "/documents/upload",
            files={"file": (path.name, pdf, "application/pdf")},
        )
    assert response.status_code == 200
    return response.json()


def test_lab_pdf_with_prescription_disclaimer_is_classified_as_lab_report():
    document = upload_pdf(CBC_PDF)
    assert document["document_type"] == "lab_report"
    names = {fact["name"] for fact in document["extracted_facts"]}
    assert {"Hemoglobin", "WBC", "Platelets", "RBC"} <= names


def test_lipid_pdf_is_classified_as_lab_report():
    document = upload_pdf(LIPID_PDF)
    assert document["document_type"] == "lab_report"


def test_prescription_pdf_is_still_classified_as_prescription():
    document = upload_pdf(PRESCRIPTION_PDF)
    assert document["document_type"] == "prescription"


def test_cbc_pdf_pipeline_verifies_end_to_end():
    document = upload_pdf(CBC_PDF)
    doc_id = document["id"]

    client.post(f"/documents/{doc_id}/confirm", json={"confirmed_facts": document["extracted_facts"]})
    client.post(f"/documents/{doc_id}/explain", json={"language": "en"})
    verification = client.post(f"/documents/{doc_id}/verify").json()

    assert verification["overall_status"] == "VERIFIED"
    assert verification["fidelity_score"] >= 90.0


def test_lipid_pdf_pipeline_verifies_end_to_end():
    document = upload_pdf(LIPID_PDF)
    doc_id = document["id"]

    client.post(f"/documents/{doc_id}/confirm", json={"confirmed_facts": document["extracted_facts"]})
    client.post(f"/documents/{doc_id}/explain", json={"language": "en"})
    verification = client.post(f"/documents/{doc_id}/verify").json()

    assert verification["overall_status"] == "VERIFIED"
    assert verification["fidelity_score"] >= 90.0
