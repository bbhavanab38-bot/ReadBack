import re
from typing import List, Dict, Any, Optional, Tuple
from app.schemas.facts import MedicalFact, FactCategory, FlagType, BoundingBox, StructuredExtractionResult
from app.schemas.navigation import VerifiedNextStep

class DocumentFactParser:
    """
    Extracts structured typed medical facts from OCR text and bounding boxes.
    Calculates confidence scores per field.
    """

    @classmethod
    def parse_document_text(
        cls,
        text: str,
        document_type: str = "lab_report",
        ocr_boxes: Optional[List[Dict[str, Any]]] = None
    ) -> StructuredExtractionResult:
        facts: List[MedicalFact] = []
        unparsed: List[str] = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        idx = 1
        for line in lines:
            # Check for lab tests
            lab_fact = cls._parse_lab_line(line, idx, ocr_boxes)
            if lab_fact:
                facts.append(lab_fact)
                idx += 1
                continue

            # Check for medications
            med_fact = cls._parse_med_line(line, idx, ocr_boxes)
            if med_fact:
                facts.append(med_fact)
                idx += 1
                continue

            # Check for instructions
            inst_fact = cls._parse_instruction_line(line, idx, ocr_boxes)
            if inst_fact:
                facts.append(inst_fact)
                idx += 1
                continue

            # Keep line in unparsed if not a header
            if len(line) > 15 and not any(h in line.lower() for h in ["patient", "doctor", "hospital", "clinic", "date", "sample"]):
                unparsed.append(line)

        # Calculate overall confidence
        avg_conf = sum(f.confidence for f in facts) / len(facts) if facts else 0.95

        return StructuredExtractionResult(
            document_type=document_type,
            patient_identifier_redacted=True,
            facts=facts,
            unparsed_sections=unparsed[:5],
            overall_confidence=round(avg_conf, 2)
        )

    @staticmethod
    def _source_page(line: str, ocr_boxes: Optional[List[Dict[str, Any]]]) -> int:
        if not ocr_boxes:
            return 1
        source_text = re.sub(r"[^a-z0-9]", "", line.lower())
        page_texts: Dict[int, str] = {}
        for box in ocr_boxes:
            page = int(box.get("page", 1))
            box_text = re.sub(r"[^a-z0-9]", "", str(box.get("text", "")).lower())
            page_texts[page] = page_texts.get(page, "") + box_text
        return next((page for page, text in page_texts.items() if source_text and source_text in text), 1)

    @classmethod
    def _parse_lab_line(cls, line: str, idx: int, ocr_boxes: Optional[List[Dict[str, Any]]]) -> Optional[MedicalFact]:
        # Regex for Lab line: Name Value Unit Range Flag
        # e.g., "Hemoglobin: 10.2 g/dL (12-16) LOW"
        # e.g., "WBC: 7800 cells/µL 4000-11000 NORMAL"
        patterns = [
            r'([A-Za-z\s\(\)]+?)[:\s]+(\d+(?:\.\d+)?)\s*([a-zA-Z/%µ\^]+)?(?:\s+(?:Ref|Range|Reference)?[:\s]*[\(\[]?(\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?)[\)\]]?)?(?:\s+(LOW|HIGH|NORMAL|CRITICAL|ABNORMAL|L|H|N))?',
        ]
        
        known_tests = [
            ("hemoglobin", "Hemoglobin"),
            ("wbc", "WBC"),
            ("rbc", "RBC"),
            ("platelets", "Platelets"),
            ("platelet count", "Platelets"),
            ("glucose", "Fasting Blood Glucose"),
            ("blood sugar", "Fasting Blood Glucose"),
            ("hba1c", "HbA1c"),
            ("creatinine", "Serum Creatinine"),
            ("tsh", "TSH"),
            ("cholesterol", "Total Cholesterol"),
            ("triglycerides", "Triglycerides"),
            ("hdl", "HDL Cholesterol"),
            ("ldl", "LDL Cholesterol"),
            ("urea", "Blood Urea"),
            ("sgot", "SGOT / AST"),
            ("sgpt", "SGPT / ALT"),
            ("bilirubin", "Total Bilirubin")
        ]

        line_low = line.lower()
        matched_test = None
        for key, name in known_tests:
            if key in line_low:
                matched_test = name
                break

        if not matched_test:
            return None

        # Extract number
        nums = re.findall(r'(\d+(?:\.\d+)?)', line)
        if not nums:
            return None
        val = float(nums[0])

        # Extract unit
        unit = None
        for u in ["g/dL", "mg/dL", "cells/µL", "cells/ul", "cells/cumm", "µIU/mL", "mIU/L", "U/L", "mg/L", "%", "mil/µL", "mil/ul"]:
            if u.lower() in line_low:
                unit = u
                break

        # Extract reference range
        ref_match = re.search(r'(\d+(?:\.\d+)?\s*[-–to ]+\s*\d+(?:\.\d+)?)', line)
        ref_range = ref_match.group(1).replace(" ", "") if ref_match and ref_match.group(1) != str(val) else None

        # Extract flag
        flag = FlagType.NONE
        flag_match = re.search(r"\b(CRITICAL|PANIC|ABNORMAL|LOW|HIGH|NORMAL|L|H|N)\b", line, re.IGNORECASE)
        if flag_match:
            flag = {
                "CRITICAL": FlagType.CRITICAL,
                "PANIC": FlagType.CRITICAL,
                "ABNORMAL": FlagType.ABNORMAL,
                "LOW": FlagType.LOW,
                "L": FlagType.LOW,
                "HIGH": FlagType.HIGH,
                "H": FlagType.HIGH,
                "NORMAL": FlagType.NORMAL,
                "N": FlagType.NORMAL,
            }[flag_match.group(1).upper()]

        # Assign confidence based on clarity and completeness
        conf = 0.98 if unit and ref_range else (0.85 if unit else 0.72)

        # Mock bounding box relative positions
        y_pos = (idx * 60) % 700 + 120
        page = cls._source_page(line, ocr_boxes)
        bbox = BoundingBox(x_min=50, y_min=y_pos, x_max=500, y_max=y_pos + 30, page=page)

        return MedicalFact(
            field_id=f"lab_{idx:03d}",
            category=FactCategory.LABORATORY,
            name=matched_test,
            value=val,
            value_type="numeric",
            unit=unit,
            reference_range=ref_range,
            flag=flag,
            source_text=line,
            page=page,
            bbox=bbox,
            confidence=conf
        )

    @classmethod
    def _parse_med_line(cls, line: str, idx: int, ocr_boxes: Optional[List[Dict[str, Any]]]) -> Optional[MedicalFact]:
        from app.services.extraction.independent_extractor import KNOWN_DRUGS
        line_low = line.lower()
        
        matched_drug = None
        for d in KNOWN_DRUGS:
            if d in line_low:
                matched_drug = d.capitalize()
                break

        if not matched_drug and not any(kw in line_low for kw in ["tablet", "tab", "capsule", "cap", "mg", "syrup"]):
            return None

        if not matched_drug:
            # Try to grab first capitalized word
            words = line.split()
            if words and words[0].isalpha():
                matched_drug = words[0]
            else:
                return None

        # Extract dosage / strength
        strength_match = re.search(r'(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml))', line, re.IGNORECASE)
        strength = strength_match.group(1) if strength_match else None

        # Extract frequency
        freq = None
        if any(f in line_low for f in ["twice", "bid", "bd", "2 times", "two times"]):
            freq = "twice daily"
        elif any(f in line_low for f in ["thrice", "tid", "tds", "3 times", "three times"]):
            freq = "three times daily"
        elif any(f in line_low for f in ["once", "daily", "qd", "od", "1 time", "one time"]):
            freq = "once daily"
        elif any(f in line_low for f in ["night", "bedtime", "hs"]):
            freq = "at bedtime"
        elif any(f in line_low for f in ["sos", "prn", "as needed"]):
            freq = "as needed"

        route_patterns = [
            ("oral", r"\b(?:by mouth|oral(?:ly)?|p\.?o\.?)\b"),
            ("topical", r"\btopical(?:ly)?\b"),
            ("intravenous", r"\b(?:intravenous|iv)\b"),
            ("intramuscular", r"\b(?:intramuscular|im)\b"),
            ("subcutaneous", r"\b(?:subcutaneous|subcutaneously|sc)\b"),
            ("inhalation", r"\b(?:inhaled|inhalation)\b"),
        ]
        route = next(
            (value for value, pattern in route_patterns if re.search(pattern, line_low)),
            None,
        )

        # Duration
        dur_match = re.search(r'(\d+\s*(?:days|weeks|months))', line_low)
        duration = dur_match.group(1) if dur_match else None

        conf = 0.95 if strength_match else 0.70
        y_pos = (idx * 55) % 700 + 150
        page = cls._source_page(line, ocr_boxes)
        bbox = BoundingBox(x_min=60, y_min=y_pos, x_max=520, y_max=y_pos + 35, page=page)

        return MedicalFact(
            field_id=f"med_{idx:03d}",
            category=FactCategory.MEDICATION,
            name=matched_drug,
            strength=strength,
            dosage=strength,
            frequency=freq,
            route=route,
            duration=duration,
            source_text=line,
            page=page,
            bbox=bbox,
            confidence=conf
        )

    @classmethod
    def _parse_instruction_line(cls, line: str, idx: int, ocr_boxes: Optional[List[Dict[str, Any]]]) -> Optional[MedicalFact]:
        line_low = line.lower()
        if not any(k in line_low for k in ["take", "avoid", "empty stomach", "meals", "food", "water", "do not", "never", "diet"]):
            return None

        has_negation = any(nm in line_low for nm in ["not", "never", "do not", "don't", "avoid"])
        
        condition = "empty stomach" if "empty stomach" in line_low else ("after food" if "after food" in line_low or "after meals" in line_low else "with water")
        action = "take medication"

        y_pos = (idx * 50) % 700 + 200
        page = cls._source_page(line, ocr_boxes)
        bbox = BoundingBox(x_min=50, y_min=y_pos, x_max=500, y_max=y_pos + 30, page=page)

        return MedicalFact(
            field_id=f"inst_{idx:03d}",
            category=FactCategory.INSTRUCTION,
            name="Medication Instruction",
            action=action,
            negation=has_negation,
            condition=condition,
            instruction_text=line,
            source_text=line,
            page=page,
            bbox=bbox,
            confidence=0.96
        )
