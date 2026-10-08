from typing import List, Dict, Any, Optional
from app.schemas.facts import MedicalFact, FactCategory, FlagType
from app.schemas.document import ExplanationResponse
from app.services.llm.provider import get_llm_provider

# Standard educational dictionary definitions for common medical terms
MEDICAL_GLOSSARY = {
    "Hemoglobin": "A protein in red blood cells that carries oxygen from your lungs to the rest of your body.",
    "WBC": "White blood cells, which are part of your immune system and help fight infections and diseases.",
    "RBC": "Red blood cells, which carry oxygen throughout your body.",
    "Platelets": "Cell fragments in your blood that help form clots to stop bleeding from cuts or injuries.",
    "Fasting Blood Glucose": "The amount of sugar in your blood after fasting (not eating) for at least 8 hours.",
    "HbA1c": "A blood test that reflects your average blood sugar levels over the past 2 to 3 months.",
    "Serum Creatinine": "A waste product produced by muscles, filtered by the kidneys, used to assess kidney function.",
    "TSH": "Thyroid Stimulating Hormone, produced by the pituitary gland to control thyroid hormone levels.",
    "Total Cholesterol": "A measurement of all cholesterol forms in your blood, including HDL and LDL.",
    "Metformin": "A commonly prescribed oral medication used to help control blood glucose levels.",
    "Metoprolol": "A beta-blocker medication often prescribed for blood pressure and heart rhythm.",
    "Atorvastatin": "A statin medication used to lower low-density lipoprotein (LDL) cholesterol."
}

class ExplanationEngine:
    """
    Generates patient-friendly explanations from confirmed structured medical facts.
    Strictly forbids diagnosis and medical advice.
    """

    @classmethod
    def generate_explanation(
        cls,
        document_id: str,
        facts: List[MedicalFact],
        language: str = "en",
        corrupt_mode: Optional[str] = None
    ) -> ExplanationResponse:
        # Build clean factual summary
        fact_lines = []
        term_definitions = {}

        for fact in facts:
            if fact.category == FactCategory.LABORATORY:
                flag_str = f", flagged as {fact.flag.value}" if fact.flag and fact.flag != FlagType.NONE else ""
                ref_str = f" (standard reference range: {fact.reference_range})" if fact.reference_range else ""
                unit_str = f" {fact.unit}" if fact.unit else ""
                line = f"• Your report shows a {fact.name} level of {fact.value}{unit_str}{ref_str}{flag_str}."
                fact_lines.append(line)
                if fact.name in MEDICAL_GLOSSARY:
                    term_definitions[fact.name] = MEDICAL_GLOSSARY[fact.name]
            elif fact.category == FactCategory.MEDICATION:
                dose_str = f" {fact.dosage or fact.strength or ''}"
                freq_str = f", to be taken {fact.frequency}" if fact.frequency else ""
                route_str = f" via {fact.route}" if fact.route else ""
                dur_str = f" for {fact.duration}" if fact.duration else ""
                line = f"• Prescribed medication: {fact.name}{dose_str}{freq_str}{route_str}{dur_str}."
                fact_lines.append(line)
                if fact.name in MEDICAL_GLOSSARY:
                    term_definitions[fact.name] = MEDICAL_GLOSSARY[fact.name]
            elif fact.category == FactCategory.INSTRUCTION:
                neg_str = "Do NOT " if fact.negation else "Please "
                cond_str = f" on/with {fact.condition}" if fact.condition else ""
                line = f"• Important instruction: {neg_str}{fact.action or 'follow directions'}{cond_str}."
                fact_lines.append(line)

        summary_text = "\n".join(fact_lines)

        # Generate through LLM provider (or mock)
        provider = get_llm_provider()
        raw_explanation = provider.generate_explanation(
            facts_summary=summary_text,
            language=language,
            corrupt_mode=corrupt_mode
        )

        return ExplanationResponse(
            document_id=document_id,
            language=language,
            explanation_text=raw_explanation,
            summary_bullet_points=fact_lines,
            term_definitions=term_definitions,
            is_safe=True
        )
