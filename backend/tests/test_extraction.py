import pytest
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import fitz
from app.services.extraction.parser import DocumentFactParser
from app.services.ocr.ocr_service import SimulatedOCRProvider, extract_document_text
from app.schemas.facts import FactCategory, FlagType

def test_extract_lab_facts():
    text = (
        "Hemoglobin: 10.2 g/dL (12.0 - 16.0) LOW\n"
        "WBC: 7800 cells/µL (4000 - 11000) NORMAL\n"
        "Platelets: 220000 cells/µL NORMAL"
    )
    result = DocumentFactParser.parse_document_text(text, document_type="lab_report")
    assert len(result.facts) == 3
    
    hb = next(f for f in result.facts if f.name == "Hemoglobin")
    assert hb.value == 10.2
    assert hb.unit == "g/dL"
    assert hb.flag == FlagType.LOW
    assert hb.confidence >= 0.85

def test_extract_prescription_facts():
    text = (
        "1. Tab. Metformin 500 mg - twice daily for 30 days\n"
        "2. Tab. Atorvastatin 20 mg - once daily\n"
        "Do NOT take on an empty stomach."
    )
    result = DocumentFactParser.parse_document_text(text, document_type="prescription")
    assert len(result.facts) >= 2
    
    met = next(f for f in result.facts if f.name == "Metformin")
    assert met.dosage == "500 mg"
    assert met.frequency == "twice daily"
    
    inst = next(f for f in result.facts if f.category == FactCategory.INSTRUCTION)
    assert inst.negation is True

def test_medication_parser_does_not_invent_missing_fields():
    result = DocumentFactParser.parse_document_text("Metformin", document_type="prescription")

    medication = next(f for f in result.facts if f.category == FactCategory.MEDICATION)
    assert medication.dosage is None
    assert medication.frequency is None
    assert medication.route is None

def test_lab_parser_does_not_invent_normal_flag():
    result = DocumentFactParser.parse_document_text("Hemoglobin: 10.2 g/dL", document_type="lab_report")

    assert result.facts[0].flag == FlagType.NONE

def test_simulated_ocr_does_not_replace_unreadable_file_with_demo_content(tmp_path):
    file_path = tmp_path / "scan.pdf"
    file_path.write_bytes(b"%PDF\xff unreadable binary content")

    result = SimulatedOCRProvider().extract_text(str(file_path))

    assert result.raw_text == ""
    assert result.confidence == 0.0


REPORT_TEXT = (
    "COMPLETE BLOOD COUNT\n"
    "Hemoglobin 10.2 g/dL (12.0 - 16.0) LOW\n"
    "Do not take the prescribed medicine on an empty stomach.\n"
    "Follow-up consultation after 2 weeks."
)


def make_report_image(image_format="PNG"):
    image = Image.new("RGB", (1800, 560), "white")
    draw = ImageDraw.Draw(image)
    draw.multiline_text(
        (60, 60),
        REPORT_TEXT,
        fill="black",
        font=ImageFont.load_default(size=36),
        spacing=30,
    )
    output = BytesIO()
    image.save(output, format=image_format)
    return image, output.getvalue()


def test_txt_is_extracted_directly(tmp_path):
    file_path = tmp_path / "report.txt"
    file_path.write_text(REPORT_TEXT, encoding="utf-8")

    result = extract_document_text(str(file_path), "paddleocr")

    assert result.raw_text == REPORT_TEXT
    assert result.page_count == 1


def test_selectable_pdf_text_is_extracted_without_ocr(tmp_path):
    file_path = tmp_path / "report.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), REPORT_TEXT)
    document.save(file_path)
    document.close()

    result = extract_document_text(str(file_path), "unavailable")

    assert "Hemoglobin 10.2" in result.raw_text
    assert result.page_count == 1


def test_scanned_pdf_pages_are_rendered_and_ocrd(tmp_path):
    image, _ = make_report_image()
    file_path = tmp_path / "scanned.pdf"
    document = fitz.open()
    page = document.new_page(width=900, height=280)
    page.insert_image(page.rect, stream=BytesIO(_image_bytes(image)).getvalue())
    document.save(file_path)
    document.close()

    result = extract_document_text(str(file_path), "paddleocr")

    assert "Hemoglobin" in result.raw_text
    assert "10.2" in result.raw_text
    assert result.page_count == 1
    assert any(box.get("page") == 1 for box in result.bounding_boxes)
    assert "Do not take the prescribed medicine on an empty stomach" in result.raw_text


@pytest.mark.parametrize("image_format, extension", [("PNG", ".png"), ("JPEG", ".jpg"), ("JPEG", ".jpeg")])
def test_png_and_jpg_images_are_ocrd(tmp_path, image_format, extension):
    _, image_bytes = make_report_image(image_format)
    file_path = tmp_path / f"report{extension}"
    file_path.write_bytes(image_bytes)

    result = extract_document_text(str(file_path), "paddleocr")

    assert "Hemoglobin" in result.raw_text
    assert "10.2" in result.raw_text


def _image_bytes(image):
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_unreadable_image_and_corrupt_pdf_return_no_text_or_raise(tmp_path):
    blank_path = tmp_path / "blank.png"
    Image.new("RGB", (400, 200), "white").save(blank_path)
    result = extract_document_text(str(blank_path), "paddleocr")
    assert result.raw_text == ""

    corrupt_path = tmp_path / "corrupt.pdf"
    corrupt_path.write_bytes(b"not a PDF")
    with pytest.raises(Exception):
        extract_document_text(str(corrupt_path), "paddleocr")


def test_scanned_pdf_fact_evidence_keeps_its_page_number(tmp_path):
    image, _ = make_report_image()
    document = fitz.open()
    document.new_page(width=900, height=280)
    page = document.new_page(width=900, height=280)
    page.insert_image(page.rect, stream=_image_bytes(image))
    file_path = tmp_path / "two-page-scan.pdf"
    document.save(file_path)
    document.close()

    result = extract_document_text(str(file_path), "paddleocr")
    parsed = DocumentFactParser.parse_document_text(result.raw_text, ocr_boxes=result.bounding_boxes)
    hemoglobin = next(fact for fact in parsed.facts if fact.name == "Hemoglobin")

    assert result.page_count == 2
    assert hemoglobin.page == 2
    assert hemoglobin.bbox.page == 2


def test_existing_synthetic_cbc_document_extracts_requested_facts():
    report_path = Path(__file__).parents[1] / "uploads" / "a4609810-5174-4b62-8561-c71d0d7eeb3f_DEMO_CBC_Blood_Report.txt"
    result = extract_document_text(str(report_path), "paddleocr")
    parsed = DocumentFactParser.parse_document_text(result.raw_text, document_type="lab_report")

    hemoglobin = next(fact for fact in parsed.facts if fact.name == "Hemoglobin")
    assert hemoglobin.value == 10.2
    assert hemoglobin.unit == "g/dL"
    assert hemoglobin.reference_range == "12.0-16.0"
    assert hemoglobin.flag == FlagType.LOW
    instruction = next(fact for fact in parsed.facts if fact.category == FactCategory.INSTRUCTION)
    assert instruction.instruction_text == "Do not take on an empty stomach."
    assert "Follow-up consultation after 2 weeks." in result.raw_text

    explicit_instruction = REPORT_TEXT.splitlines()[2]
    instruction_result = DocumentFactParser.parse_document_text(explicit_instruction)
    assert instruction_result.facts[0].instruction_text == explicit_instruction
