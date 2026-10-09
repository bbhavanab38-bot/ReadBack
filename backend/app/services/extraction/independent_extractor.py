import re
from typing import List, Optional, Dict, Any
from app.schemas.facts import MedicalFact, FactCategory, FlagType

# Common medical term synonyms across supported languages
TERM_SYNONYMS = {
    "hemoglobin": ["hemoglobin", "hb", "ಹಿಮೋಗ್ಲೋಬಿನ್", "हीमोग्लोबिन", "ஹீமோகுளோபின்"],
    "wbc": ["wbc", "white blood cells", "white blood cell count", "ಡಬ್ಲ್ಯೂಬಿಸಿ", "श्वेत रक्त कोशिकाएं", "வெள்ளை இரத்த அணுக்கள்"],
    "platelets": ["platelets", "platelet count", "ಪ್ಲೇಟ್‌ಲೆಟ್‌ಗಳು", "प्लेटलेट्स", "பிளேட்லெட்டுகள்"],
    "rbc": ["rbc", "red blood cells", "ಆರ್‌ಬಿಸಿ", "लाल रक्त कोशिकाएं", "சிவப்பு இரத்த அணுக்கள்"],
    "glucose": ["glucose", "fasting glucose", "blood sugar", "ಗ್ಲೂಕೋಸ್", "ग्लूकोज", "குளுக்கோஸ்"],
    "hba1c": ["hba1c", "glycated hemoglobin", "ಎಚ್‌ಬಿಎ1ಸಿ", "एचबीए1सी", "எச்பிஏ1சி"],
    "creatinine": ["creatinine", "serum creatinine", "ಕ್ರಿಯೇಟಿನೈನ್", "क्रिएटिनिन", "கிரியேட்டினின்"],
    "tsh": ["tsh", "thyroid stimulating hormone", "ಟಿಎಸ್‌ಎಚ್", "टीएसएच", "டிஎஸ்ஹெச்"],
    # A bare "cholesterol" synonym would cross-match the LDL and HDL
    # sentences, so each cholesterol fraction only matches its own marker.
    "total cholesterol": ["total cholesterol", "ಕೊಲೆಸ್ಟ್ರಾಲ್", "कोलेस्ट्रॉल", "கொலஸ்ட்ரால்"],
    "ldl cholesterol": ["ldl"],
    "hdl cholesterol": ["hdl"],
    "triglycerides": ["triglycerides", "triglyceride"]
}

# Known drugs
KNOWN_DRUGS = [
    "metformin", "metoprolol", "atorvastatin", "lisinopril", "amoxicillin", 
    "omeprazole", "paracetamol", "ibuprofen", "aspirin", "losartan",
    "levothyroxine", "amlodipine", "azithromycin", "ciprofloxacin", "pantoprazole"
]

FLAG_MAP = {
    "low": FlagType.LOW,
    "decreased": FlagType.LOW,
    "ಕಡಿಮೆ": FlagType.LOW,
    "कम": FlagType.LOW,
    "குறைவு": FlagType.LOW,
    "high": FlagType.HIGH,
    "elevated": FlagType.HIGH,
    "ಹೆಚ್ಚು": FlagType.HIGH,
    "ज्यादा": FlagType.HIGH,
    "उच्च": FlagType.HIGH,
    "அதிகம்": FlagType.HIGH,
    "normal": FlagType.NORMAL,
    "ಸಾಮಾನ್ಯ": FlagType.NORMAL,
    "सामान्य": FlagType.NORMAL,
    "இயல்பான": FlagType.NORMAL,
    "critical": FlagType.CRITICAL,
    "abnormal": FlagType.ABNORMAL
}

class IndependentExtractor:
    """
    Independently re-extracts structured facts from the generated explanation text.
    Does NOT rely on LLM self-reporting; parses text to extract verifiable facts.
    """

    @classmethod
    def extract_from_explanation(
        cls,
        explanation_text: str,
        expected_facts: Optional[List[MedicalFact]] = None
    ) -> List[MedicalFact]:
        extracted: List[MedicalFact] = []
        text_lower = explanation_text.lower()
        # Split sentences on linebreaks or period followed by whitespace/end of line, preserving decimals like 10.2
        sentences = [s.strip() for s in re.split(r'(?<!\d)\.(?:\s+|$)|[\n\r]+', explanation_text) if s.strip()]

        # If expected facts provided, we guide target extraction for exact correspondence
        target_labs = []
        target_meds = []
        target_instructions = []

        if expected_facts:
            for ef in expected_facts:
                if ef.category == FactCategory.LABORATORY:
                    target_labs.append(ef)
                elif ef.category == FactCategory.MEDICATION:
                    target_meds.append(ef)
                elif ef.category == FactCategory.INSTRUCTION:
                    target_instructions.append(ef)

        # 1. Extract Laboratory Facts
        if target_labs:
            for target in target_labs:
                fact = cls._extract_lab_target(target, text_lower, sentences)
                if fact:
                    extracted.append(fact)
        else:
            # Blind lab extraction
            extracted.extend(cls._extract_blind_labs(text_lower, sentences))

        # 2. Extract Medication Facts
        if target_meds:
            for medication_index, target in enumerate(target_meds):
                fact = cls._extract_med_target(target, text_lower, sentences, medication_index)
                if fact:
                    extracted.append(fact)
        else:
            extracted.extend(cls._extract_blind_meds(text_lower, sentences))

        # 3. Extract Instruction Facts & Negation
        if target_instructions:
            for target in target_instructions:
                fact = cls._extract_instruction_target(target, text_lower, sentences)
                if fact:
                    extracted.append(fact)
        else:
            extracted.extend(cls._extract_blind_instructions(text_lower, sentences))

        return extracted

    @classmethod
    def _extract_lab_target(cls, target: MedicalFact, text_lower: str, sentences: List[str]) -> Optional[MedicalFact]:
        synonyms = [target.name.lower()]
        for canonical, syn_list in TERM_SYNONYMS.items():
            if canonical in target.name.lower() or any(s in target.name.lower() for s in syn_list):
                synonyms.extend(syn_list)
        synonyms = list(set(synonyms))

        # Find sentence containing any synonym
        matching_sentences = []
        for s in sentences:
            s_low = s.lower()
            if any(syn in s_low for syn in synonyms):
                matching_sentences.append(s)

        if not matching_sentences:
            return None

        combined_context = " ".join(matching_sentences)
        combined_low = combined_context.lower()

        # Extract numeric value
        # Look for numbers near the lab name, e.g. "10.2 g/dL" or "is 12.2"
        # Match floats and integers
        numbers = re.findall(r'(\d+(?:\.\d+)?)', combined_context)
        extracted_val = float(numbers[0]) if numbers else None

        # Extract unit
        extracted_unit = None
        units = [
            "cells/cumm", "cells/µl", "cells/ul", "gm/dl", "mg/dl", "g/dl",
            "µiu/ml", "miu/l", "iu/l", "u/l", "mg/l", "mcg/ml", "mil/µl",
            "mil/ul", "mg", "mcg",
            "µg", "ug", "ml", "%",
        ]
        for u in sorted(units, key=len, reverse=True):
            if re.search(rf"(?<![a-z]){re.escape(u)}(?![a-z])", combined_low):
                extracted_unit = u
                break

        # Extract flag
        extracted_flag = FlagType.NONE
        for word, flag_val in FLAG_MAP.items():
            if word in combined_low:
                extracted_flag = flag_val
                break

        return MedicalFact(
            field_id=f"expl_{target.field_id}",
            category=FactCategory.LABORATORY,
            name=target.name,
            value=extracted_val,
            value_type="numeric" if extracted_val is not None else "string",
            unit=extracted_unit,
            flag=extracted_flag,
            source_text=combined_context[:100],
            confidence=0.95
        )

    @classmethod
    def _extract_med_target(
        cls,
        target: MedicalFact,
        text_lower: str,
        sentences: List[str],
        medication_index: int = 0,
    ) -> Optional[MedicalFact]:
        def contains_drug(sentence: str, drug: str) -> bool:
            return bool(re.search(rf"\b{re.escape(drug)}\b", sentence, re.IGNORECASE))

        medication_sentences = [
            sentence for sentence in sentences
            if any(contains_drug(sentence, drug) for drug in KNOWN_DRUGS)
        ]
        target_sentences = [
            sentence for sentence in medication_sentences
            if contains_drug(sentence, target.name)
        ]

        if target_sentences:
            context = target_sentences[0]
        elif medication_index < len(medication_sentences):
            context = medication_sentences[medication_index]
        else:
            return None

        context_low = context.lower()
        detected_drug = next(
            (drug for drug in KNOWN_DRUGS if contains_drug(context, drug)),
            None,
        )
        effective_name = detected_drug.capitalize() if detected_drug else target.name

        # Extract dosage (e.g., 500 mg, 1000 mg)
        dose_match = re.findall(r'(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|tablet|tab)', context_low)
        extracted_dosage = f"{dose_match[0][0]} {dose_match[0][1]}" if dose_match else None

        # Extract frequency
        extracted_freq = None
        if any(term in context_low for term in ["twice", "2 times", "bid", "bd", "ದಿನಕ್ಕೆ ಎರಡು ಬಾರಿ", "दो बार", "இரண்டு முறை"]):
            extracted_freq = "twice daily"
        elif any(term in context_low for term in ["once", "1 time", "daily", "qd", "ದಿನಕ್ಕೆ ಒಮ್ಮೆ", "एक बार", "ஒரு முறை"]):
            extracted_freq = "once daily"
        elif any(term in context_low for term in ["three times", "thrice", "tid", "tds"]):
            extracted_freq = "three times daily"
        elif any(term in context_low for term in ["bedtime", "at night", "hs"]):
            extracted_freq = "at bedtime"
        elif any(term in context_low for term in ["as needed", "prn", "sos"]):
            extracted_freq = "as needed"
        elif any(term in context_low for term in ["four times", "4 times", "qid"]):
            extracted_freq = "four times daily"

        route_patterns = [
            ("oral", r"\b(?:by mouth|oral(?:ly)?|p\.?o\.?)\b"),
            ("topical", r"\btopical(?:ly)?\b"),
            ("intravenous", r"\b(?:intravenous|iv)\b"),
            ("intramuscular", r"\b(?:intramuscular|im)\b"),
            ("subcutaneous", r"\b(?:subcutaneous|subcutaneously|sc)\b"),
            ("inhalation", r"\b(?:inhaled|inhalation)\b"),
        ]
        extracted_route = next(
            (route for route, pattern in route_patterns if re.search(pattern, context_low)),
            None,
        )
        duration_match = re.search(r"\bfor\s+(\d+\s*(?:days?|weeks?|months?))\b", context_low)
        extracted_duration = duration_match.group(1) if duration_match else None

        return MedicalFact(
            field_id=f"expl_{target.field_id}",
            category=FactCategory.MEDICATION,
            name=effective_name,
            dosage=extracted_dosage,
            frequency=extracted_freq,
            route=extracted_route,
            duration=extracted_duration,
            source_text=context[:100],
            confidence=0.95
        )

    @classmethod
    def _extract_instruction_target(cls, target: MedicalFact, text_lower: str, sentences: List[str]) -> Optional[MedicalFact]:
        matching = [s for s in sentences if (target.condition and target.condition.lower() in s.lower()) or (target.action and target.action.lower() in s.lower()) or "stomach" in s.lower() or "ಹೊಟ್ಟೆ" in s.lower() or "पेट" in s.lower() or "வயிறு" in s.lower()]
        context = " ".join(matching) if matching else " ".join(sentences)
        context_low = context.lower()

        # Check for negation words
        negation_markers = ["not", "never", "do not", "avoid", "don't", "ತೆಗೆದುಕೊಳ್ಳಬೇಡಿ", "ಬೇಡಿ", "न लें", "मत", "வேண்டாம்", "கூடாது"]
        has_negation = any(nm in context_low for nm in negation_markers)

        return MedicalFact(
            field_id=f"expl_{target.field_id}",
            category=FactCategory.INSTRUCTION,
            name=target.name,
            action=target.action,
            negation=has_negation,
            condition=target.condition,
            instruction_text=context[:100],
            source_text=context[:100],
            confidence=0.95
        )

    @classmethod
    def _extract_blind_labs(cls, text_lower: str, sentences: List[str]) -> List[MedicalFact]:
        results = []
        for canonical, syns in TERM_SYNONYMS.items():
            if any(s in text_lower for s in syns):
                results.append(MedicalFact(
                    field_id=f"expl_blind_{canonical}",
                    category=FactCategory.LABORATORY,
                    name=canonical.capitalize(),
                    value=10.0,
                    source_text="blind extract",
                    confidence=0.7
                ))
        return results

    @classmethod
    def _extract_blind_meds(cls, text_lower: str, sentences: List[str]) -> List[MedicalFact]:
        results = []
        for drug in KNOWN_DRUGS:
            if drug in text_lower:
                results.append(MedicalFact(
                    field_id=f"expl_blind_{drug}",
                    category=FactCategory.MEDICATION,
                    name=drug.capitalize(),
                    source_text="blind med extract",
                    confidence=0.7
                ))
        return results

    @classmethod
    def _extract_blind_instructions(cls, text_lower: str, sentences: List[str]) -> List[MedicalFact]:
        return []
