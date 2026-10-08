import re
from typing import List, Optional

from app.schemas.facts import FactCategory, MedicalFact
from app.schemas.fidelity import FidelityFailureType, FidelitySimulationResponse
from app.schemas.verification import VerificationStatus
from app.services.extraction.independent_extractor import IndependentExtractor, KNOWN_DRUGS
from app.services.verification.engine import VerificationEngine


class FidelitySimulationError(ValueError):
    pass


def _find_fact(
    facts: List[MedicalFact],
    category: FactCategory,
    predicate,
) -> Optional[MedicalFact]:
    return next((fact for fact in facts if fact.category == category and predicate(fact)), None)


def _claim_line(explanation: str, fact: MedicalFact) -> tuple[List[str], int]:
    lines = explanation.splitlines()
    terms = [fact.name, fact.condition, fact.action]
    terms = [term.lower() for term in terms if term]
    for index, line in enumerate(lines):
        if any(term in line.lower() for term in terms):
            return lines, index
    raise FidelitySimulationError(f"Could not locate {fact.name} in the verified explanation.")


def _format_number(value) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:g}"


def _replace_once(text: str, old: str, new: str, *, ignore_case: bool = False) -> str:
    match = re.search(re.escape(old), text, re.IGNORECASE if ignore_case else 0)
    if not match:
        raise FidelitySimulationError(f"Could not locate '{old}' in the verified explanation.")
    return f"{text[:match.start()]}{new}{text[match.end():]}"


def _select_target(facts: List[MedicalFact], failure_type: FidelityFailureType) -> MedicalFact:
    if failure_type in {
        FidelityFailureType.NUMERIC_VALUE_CHANGED,
        FidelityFailureType.UNIT_CHANGED,
        FidelityFailureType.ABNORMAL_FLAG_CHANGED,
    }:
        target = _find_fact(
            facts,
            FactCategory.LABORATORY,
            lambda fact: fact.value is not None
            and (failure_type != FidelityFailureType.UNIT_CHANGED or bool(fact.unit))
            and (failure_type != FidelityFailureType.ABNORMAL_FLAG_CHANGED or bool(fact.flag)),
        )
    elif failure_type in {
        FidelityFailureType.DRUG_NAME_CHANGED,
        FidelityFailureType.DOSAGE_CHANGED,
        FidelityFailureType.FREQUENCY_CHANGED,
    }:
        target = _find_fact(
            facts,
            FactCategory.MEDICATION,
            lambda fact: failure_type == FidelityFailureType.DRUG_NAME_CHANGED
            or (failure_type == FidelityFailureType.DOSAGE_CHANGED and bool(fact.dosage or fact.strength))
            or (failure_type == FidelityFailureType.FREQUENCY_CHANGED and bool(fact.frequency)),
        )
    elif failure_type == FidelityFailureType.NEGATION_FLIPPED:
        target = _find_fact(facts, FactCategory.INSTRUCTION, lambda fact: True)
    else:
        target = next(
            (
                fact for fact in facts
                if fact.category in {FactCategory.LABORATORY, FactCategory.MEDICATION}
                or (fact.category == FactCategory.INSTRUCTION and fact.negation)
            ),
            None,
        )

    if not target:
        raise FidelitySimulationError(f"This document has no field suitable for {failure_type.value}.")
    return target


def _corrupt_claim(explanation: str, fact: MedicalFact, failure_type: FidelityFailureType) -> str:
    lines, index = _claim_line(explanation, fact)
    line = lines[index]

    if failure_type == FidelityFailureType.NUMERIC_VALUE_CHANGED:
        value = _format_number(fact.value)
        corrupted = _format_number(float(fact.value) + 2.0)
        lines[index] = _replace_once(line, value, corrupted)
    elif failure_type == FidelityFailureType.UNIT_CHANGED:
        unit = fact.unit or ""
        corrupted = "mg/dL" if unit.lower() != "mg/dl" else "g/dL"
        lines[index] = _replace_once(line, unit, corrupted, ignore_case=True)
    elif failure_type == FidelityFailureType.DRUG_NAME_CHANGED:
        replacement = next((drug.capitalize() for drug in KNOWN_DRUGS if drug != fact.name.lower()), None)
        if not replacement:
            raise FidelitySimulationError("No alternate known medication is available for this demonstration.")
        lines[index] = _replace_once(line, fact.name, replacement, ignore_case=True)
    elif failure_type == FidelityFailureType.DOSAGE_CHANGED:
        dosage = fact.dosage or fact.strength or ""
        match = re.search(r"\d+(?:\.\d+)?", dosage)
        if not match:
            raise FidelitySimulationError(f"Could not parse dosage '{dosage}'.")
        current = float(match.group())
        replacement = "1000" if current != 1000 else "250"
        corrupted = f"{replacement}{dosage[match.end():]}"
        lines[index] = _replace_once(line, dosage, corrupted, ignore_case=True)
    elif failure_type == FidelityFailureType.FREQUENCY_CHANGED:
        frequency = fact.frequency or ""
        corrupted = "once daily" if "once" not in frequency.lower() else "twice daily"
        lines[index] = _replace_once(line, frequency, corrupted, ignore_case=True)
    elif failure_type == FidelityFailureType.NEGATION_FLIPPED:
        if fact.negation:
            updated, count = re.subn(r"\b(?:do\s+not|don't|never|avoid)\b", "Please", line, count=1, flags=re.IGNORECASE)
        else:
            updated, count = re.subn(r"\b(take|consume|drink|avoid)\b", r"Do NOT \1", line, count=1, flags=re.IGNORECASE)
        if not count:
            raise FidelitySimulationError("Could not safely flip negation in the selected instruction.")
        lines[index] = updated
    elif failure_type == FidelityFailureType.ABNORMAL_FLAG_CHANGED:
        flag = str(fact.flag.value if hasattr(fact.flag, "value") else fact.flag)
        opposite = {"LOW": "NORMAL", "HIGH": "NORMAL", "NORMAL": "LOW", "CRITICAL": "NORMAL", "ABNORMAL": "NORMAL"}.get(flag.upper(), "NORMAL")
        lines[index] = _replace_once(line, flag, opposite, ignore_case=True)
    elif failure_type == FidelityFailureType.IMPORTANT_FACT_OMITTED:
        del lines[index]
    else:
        raise FidelitySimulationError(f"Unsupported failure type: {failure_type.value}")

    return "\n".join(lines)


def simulate_ai_error(
    document_id: str,
    explanation: str,
    facts: List[MedicalFact],
    failure_type: FidelityFailureType,
) -> FidelitySimulationResponse:
    baseline_facts = IndependentExtractor.extract_from_explanation(explanation, facts)
    baseline_result = VerificationEngine.verify(facts, baseline_facts)
    if baseline_result.overall_status != VerificationStatus.VERIFIED or not baseline_result.explanation_safe_to_display:
        raise FidelitySimulationError("Simulation requires an explanation that passes current ReadBack verification.")

    target = _select_target(facts, failure_type)
    corrupted_explanation = _corrupt_claim(explanation, target, failure_type)
    reextracted_facts = IndependentExtractor.extract_from_explanation(corrupted_explanation, facts)
    result = VerificationEngine.verify(facts, reextracted_facts)

    return FidelitySimulationResponse(
        document_id=document_id,
        failure_type=failure_type,
        original_explanation=explanation,
        simulated_explanation=corrupted_explanation,
        original_facts=facts,
        reextracted_facts=reextracted_facts,
        verification_result=result,
    )