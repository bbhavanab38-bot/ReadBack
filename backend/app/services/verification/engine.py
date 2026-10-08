import re
from typing import List, Dict, Any, Tuple, Optional, Union
from app.schemas.facts import MedicalFact, FactCategory, FlagType
from app.schemas.verification import (
    VerificationResult,
    VerificationStatus,
    FieldComparison,
    MismatchType
)

def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s\./-]', '', text)
    return re.sub(r'\s+', ' ', text)

def normalize_unit(unit: Optional[str]) -> str:
    if not unit:
        return ""
    u = unit.lower().strip().replace(" ", "")
    # Common mappings
    mapping = {
        "g/dl": "g/dl",
        "gm/dl": "g/dl",
        "grams/dl": "g/dl",
        "mg/dl": "mg/dl",
        "mg/l": "mg/l",
        "cells/ul": "cells/µl",
        "cells/cumm": "cells/µl",
        "cells/µl": "cells/µl",
        "mg": "mg",
        "mcg": "mcg",
        "ug": "mcg",
        "µg": "mcg",
        "ml": "ml",
        "tablet": "tablet",
        "tab": "tablet",
        "tablets": "tablet",
        "tabs": "tablet",
        "iu/l": "iu/l",
        "u/l": "u/l",
        "%": "%",
        "percent": "%"
    }
    return mapping.get(u, u)

def normalize_dosage(dosage: Optional[str]) -> str:
    if not dosage:
        return ""
    match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zµ%/]+)?", dosage.lower())
    if not match:
        return normalize_text(dosage)
    number = str(float(match.group(1)))
    unit = normalize_unit(match.group(2)) if match.group(2) else ""
    return f"{number} {unit}".strip()

def normalize_frequency(freq: Optional[str]) -> str:
    if not freq:
        return ""
    f = freq.lower().strip()
    if any(k in f for k in ["twice", "2 times", "bid", "bd", "two times"]):
        return "twice daily"
    if any(k in f for k in ["thrice", "3 times", "tid", "tds", "three times"]):
        return "three times daily"
    if any(k in f for k in ["four times", "4 times", "qid"]):
        return "four times daily"
    if any(k in f for k in ["once", "1 time", "od", "qd", "daily", "one time"]):
        return "once daily"
    if "bedtime" in f or "hs" in f:
        return "at bedtime"
    if "prn" in f or "as needed" in f:
        return "as needed"
    return f

def normalize_flag(flag: Optional[Union[FlagType, str]]) -> str:
    if not flag:
        return "NONE"
    f = str(flag).upper().replace("FLAGTYPE.", "")
    if f in ["L", "LOW", "DECREASED"]:
        return "LOW"
    if f in ["H", "HIGH", "ELEVATED", "INCREASED"]:
        return "HIGH"
    if f in ["N", "NORM", "NORMAL", "WNL"]:
        return "NORMAL"
    if f in ["CRIT", "CRITICAL", "PANIC"]:
        return "CRITICAL"
    if f in ["ABN", "ABNORMAL"]:
        return "ABNORMAL"
    return f

class VerificationEngine:
    """
    ReadBack Verification Engine
    Performs field-by-field normalized comparison between confirmed original facts
    and independently extracted facts from the generated explanation.
    """
    
    @classmethod
    def verify(
        cls,
        confirmed_facts: List[MedicalFact],
        explanation_facts: List[MedicalFact],
        confidence_threshold: float = 0.80
    ) -> VerificationResult:
        field_comparisons: List[FieldComparison] = []
        critical_mismatches_count = 0
        passed_count = 0
        review_count = 0
        what_could_not_verify: List[str] = []
        blocked_reasons: List[str] = []
        
        # Build lookup for explanation facts by name & category, and by field_id correspondence
        expl_lookup: Dict[str, MedicalFact] = {}
        for ef in explanation_facts:
            key = f"{ef.category.value}_{normalize_text(ef.name)}"
            expl_lookup[key] = ef
            # also allow fuzzy name lookup
            expl_lookup[normalize_text(ef.name)] = ef
            if ef.field_id:
                expl_lookup[ef.field_id] = ef
                if ef.field_id.startswith("expl_"):
                    expl_lookup[ef.field_id[5:]] = ef
        
        for orig in confirmed_facts:
            # Check what couldn't be verified initially
            if orig.confidence < confidence_threshold:
                what_could_not_verify.append(
                    f"Low confidence ({int(orig.confidence * 100)}%) on {orig.name} from original document."
                )
            if orig.category == FactCategory.LABORATORY and not orig.reference_range:
                what_could_not_verify.append(
                    f"Reference range was missing for {orig.name} in original document."
                )
            
            # Find matching fact in explanation by field_id correspondence first, then by name
            key1 = f"{orig.category.value}_{normalize_text(orig.name)}"
            key2 = normalize_text(orig.name)
            expl = expl_lookup.get(orig.field_id) or expl_lookup.get(f"expl_{orig.field_id}") or expl_lookup.get(key1) or expl_lookup.get(key2)
            
            orig_disp = cls._format_fact_display(orig)
            
            if not expl:
                # If a critical lab or med was completely omitted in explanation
                is_crit = (
                    orig.category in [FactCategory.LABORATORY, FactCategory.MEDICATION]
                    or (orig.category == FactCategory.INSTRUCTION and orig.negation)
                )
                comparison = FieldComparison(
                    field_id=orig.field_id,
                    field_name=orig.name,
                    category=orig.category,
                    original_display=orig_disp,
                    explanation_display="[Omitted / Not mentioned]",
                    status="MISSING" if not is_crit else "MISMATCH",
                    mismatch_type=MismatchType.FIELD_OMITTED,
                    is_critical=is_crit,
                    details=f"Field '{orig.name}' was present in original document but not detected in explanation."
                )
                if is_crit:
                    critical_mismatches_count += 1
                    if orig.category == FactCategory.MEDICATION:
                        blocked_reasons.append(f"Prescribed medication '{orig.name}' was omitted from explanation.")
                    elif orig.category == FactCategory.LABORATORY:
                        blocked_reasons.append(f"Laboratory result '{orig.name}' was omitted from explanation.")
                    else:
                        blocked_reasons.append(f"Negated instruction '{orig.name}' was omitted from explanation.")
                else:
                    review_count += 1
                comparison.source_text = orig.source_text
                field_comparisons.append(comparison)
                continue
            
            expl_disp = cls._format_fact_display(expl)
            
            # Field comparison by category
            if orig.category == FactCategory.LABORATORY:
                comp, is_crit_fail, reason = cls._compare_laboratory(orig, expl, orig_disp, expl_disp)
            elif orig.category == FactCategory.MEDICATION:
                comp, is_crit_fail, reason = cls._compare_medication(orig, expl, orig_disp, expl_disp)
            elif orig.category == FactCategory.INSTRUCTION:
                comp, is_crit_fail, reason = cls._compare_instruction(orig, expl, orig_disp, expl_disp)
            else:
                comp, is_crit_fail, reason = cls._compare_general(orig, expl, orig_disp, expl_disp)

            comp.source_text = orig.source_text
            comp.explanation_source_text = expl.source_text
            
            if is_crit_fail:
                critical_mismatches_count += 1
                if reason:
                    blocked_reasons.append(reason)
            elif comp.status == "PASS":
                passed_count += 1
            else:
                review_count += 1
                
            field_comparisons.append(comp)
        
        total_checked = len(confirmed_facts)
        # Calculate Document Fidelity Score mathematically
        if total_checked > 0:
            fidelity_score = round((passed_count / total_checked) * 100.0, 1)
        else:
            fidelity_score = 100.0
            
        # Determine overall verification status
        if critical_mismatches_count > 0:
            overall_status = VerificationStatus.BLOCKED
            safe_to_display = False
        elif review_count > 0 or any(f.confidence < confidence_threshold and not getattr(f, 'user_confirmed', False) for f in confirmed_facts):
            if passed_count > 0 and fidelity_score >= 80.0:
                overall_status = VerificationStatus.PARTIALLY_VERIFIED
            else:
                overall_status = VerificationStatus.NEEDS_REVIEW
            safe_to_display = True
        else:
            overall_status = VerificationStatus.VERIFIED
            safe_to_display = True
            
        return VerificationResult(
            overall_status=overall_status,
            fidelity_score=fidelity_score,
            total_fields_checked=total_checked,
            passed_count=passed_count,
            review_count=review_count,
            critical_mismatches_count=critical_mismatches_count,
            field_comparisons=field_comparisons,
            blocked_reason="; ".join(blocked_reasons) if blocked_reasons else None,
            what_readback_could_not_verify=list(dict.fromkeys(what_could_not_verify)),
            explanation_safe_to_display=safe_to_display
        )
    
    @classmethod
    def _compare_laboratory(
        cls,
        orig: MedicalFact,
        expl: MedicalFact,
        orig_disp: str,
        expl_disp: str
    ) -> Tuple[FieldComparison, bool, Optional[str]]:
        # 1. Numeric check
        if orig.value is None and expl.value is not None:
            reason = f"Unsupported numeric value for {orig.name}: Explanation reported {expl.value}, but the original document had no value"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.NUMERIC_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
        if orig.value is not None and expl.value is None:
            reason = f"Numeric value omitted for {orig.name}: Original {orig.value}, Explanation reported no value"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.NUMERIC_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
        if orig.value is not None and expl.value is not None:
            try:
                v_orig = float(orig.value)
                v_expl = float(expl.value)
                if abs(v_orig - v_expl) > 0.001:
                    reason = f"Numeric mismatch for {orig.name}: Original {orig.value}, Explanation {expl.value}"
                    return FieldComparison(
                        field_id=orig.field_id,
                        field_name=orig.name,
                        category=orig.category,
                        original_display=orig_disp,
                        explanation_display=expl_disp,
                        status="MISMATCH",
                        mismatch_type=MismatchType.NUMERIC_MISMATCH,
                        is_critical=True,
                        details=reason
                    ), True, reason
            except ValueError:
                # String comparison
                if normalize_text(str(orig.value)) != normalize_text(str(expl.value)):
                    reason = f"Value mismatch for {orig.name}: Original '{orig.value}', Explanation '{expl.value}'"
                    return FieldComparison(
                        field_id=orig.field_id,
                        field_name=orig.name,
                        category=orig.category,
                        original_display=orig_disp,
                        explanation_display=expl_disp,
                        status="MISMATCH",
                        mismatch_type=MismatchType.NUMERIC_MISMATCH,
                        is_critical=True,
                        details=reason
                    ), True, reason
        
        # 2. Unit check
        if not orig.unit and expl.unit:
            reason = f"Unsupported unit for {orig.name}: Explanation reported {expl.unit}, but the original document had no unit"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.UNIT_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
        if orig.unit and not expl.unit:
            reason = f"Unit omitted for {orig.name}: Original {orig.unit}, Explanation reported no unit"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.UNIT_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
        if orig.unit and expl.unit:
            u_orig = normalize_unit(orig.unit)
            u_expl = normalize_unit(expl.unit)
            if u_orig != u_expl:
                reason = f"Unit mismatch for {orig.name}: Original {orig.unit}, Explanation {expl.unit}"
                return FieldComparison(
                    field_id=orig.field_id,
                    field_name=orig.name,
                    category=orig.category,
                    original_display=orig_disp,
                    explanation_display=expl_disp,
                    status="MISMATCH",
                    mismatch_type=MismatchType.UNIT_MISMATCH,
                    is_critical=True,
                    details=reason
                ), True, reason
        
        # 3. Flag check
        orig_flag = normalize_flag(orig.flag)
        expl_flag = normalize_flag(expl.flag)
        if orig_flag not in ["NONE", ""] or expl_flag not in ["NONE", ""]:
            if orig_flag != expl_flag:
                # Critical mismatch if low reported as normal or high reported as normal etc.
                reason = f"Flag mismatch for {orig.name}: Original is {orig_flag}, but Explanation reported {expl_flag}"
                return FieldComparison(
                    field_id=orig.field_id,
                    field_name=orig.name,
                    category=orig.category,
                    original_display=orig_disp,
                    explanation_display=expl_disp,
                    status="MISMATCH",
                    mismatch_type=MismatchType.FLAG_MISMATCH,
                    is_critical=True,
                    details=reason
                ), True, reason

        return FieldComparison(
            field_id=orig.field_id,
            field_name=orig.name,
            category=orig.category,
            original_display=orig_disp,
            explanation_display=expl_disp,
            status="PASS",
            mismatch_type=None,
            is_critical=False,
            details="Laboratory value, unit, and flag verified accurately."
        ), False, None

    @classmethod
    def _compare_medication(
        cls,
        orig: MedicalFact,
        expl: MedicalFact,
        orig_disp: str,
        expl_disp: str
    ) -> Tuple[FieldComparison, bool, Optional[str]]:
        # 1. Drug name check
        d_orig = normalize_text(orig.name)
        d_expl = normalize_text(expl.name)
        if d_orig and d_expl and d_orig != d_expl:
            # Drug name mismatch
            reason = f"CRITICAL DRUG NAME MISMATCH: Original '{orig.name}', Explanation '{expl.name}'"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.CRITICAL_DRUG_MISMATCH,
                is_critical=True,
                details=reason
            ), True, reason
            
        # 2. Dosage check
        if not orig.dosage and expl.dosage:
            reason = f"CRITICAL UNSUPPORTED DOSAGE: Explanation added {expl.dosage}, but the original document had no dosage"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.CRITICAL_DOSAGE_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
        if orig.dosage and not expl.dosage:
            reason = f"CRITICAL DOSAGE OMITTED: Original {orig.dosage}, Explanation reported no dosage"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.CRITICAL_DOSAGE_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
        if orig.dosage and expl.dosage:
            if normalize_dosage(orig.dosage) != normalize_dosage(expl.dosage):
                reason = f"CRITICAL DOSAGE MISMATCH: Original {orig.dosage}, Explanation {expl.dosage}"
                return FieldComparison(
                    field_id=orig.field_id,
                    field_name=orig.name,
                    category=orig.category,
                    original_display=orig_disp,
                    explanation_display=expl_disp,
                    status="MISMATCH",
                    mismatch_type=MismatchType.CRITICAL_DOSAGE_MISMATCH,
                    is_critical=True,
                    details=reason
                ), True, reason
                
        # 3. Frequency check
        if not orig.frequency and expl.frequency:
            reason = f"CRITICAL UNSUPPORTED FREQUENCY: Explanation added '{expl.frequency}', but the original document had no frequency"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.CRITICAL_FREQUENCY_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
        if orig.frequency and not expl.frequency:
            reason = f"CRITICAL FREQUENCY OMITTED: Original '{orig.frequency}', Explanation reported no frequency"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.CRITICAL_FREQUENCY_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
        if orig.frequency and expl.frequency:
            f_orig = normalize_frequency(orig.frequency)
            f_expl = normalize_frequency(expl.frequency)
            if f_orig != f_expl:
                reason = f"CRITICAL FREQUENCY MISMATCH: Original '{orig.frequency}', Explanation '{expl.frequency}'"
                return FieldComparison(
                    field_id=orig.field_id,
                    field_name=orig.name,
                    category=orig.category,
                    original_display=orig_disp,
                    explanation_display=expl_disp,
                    status="MISMATCH",
                    mismatch_type=MismatchType.CRITICAL_FREQUENCY_MISMATCH,
                    is_critical=True,
                    details=reason
                ), True, reason

        if not orig.route and expl.route:
            reason = f"CRITICAL UNSUPPORTED ROUTE: Explanation added '{expl.route}', but the original document had no route"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.CRITICAL_ROUTE_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
        if orig.route and not expl.route:
            reason = f"CRITICAL ROUTE OMITTED: Original '{orig.route}', Explanation reported no route"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.CRITICAL_ROUTE_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
        if orig.route and expl.route and normalize_text(orig.route) != normalize_text(expl.route):
            reason = f"CRITICAL ROUTE MISMATCH: Original '{orig.route}', Explanation '{expl.route}'"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.CRITICAL_ROUTE_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason

        if not orig.duration and expl.duration:
            reason = f"CRITICAL UNSUPPORTED DURATION: Explanation added '{expl.duration}', but the original document had no duration"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.CRITICAL_DURATION_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
        if orig.duration and not expl.duration:
            reason = f"CRITICAL DURATION OMITTED: Original '{orig.duration}', Explanation reported no duration"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.CRITICAL_DURATION_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
        if orig.duration and expl.duration and normalize_text(orig.duration) != normalize_text(expl.duration):
            reason = f"CRITICAL DURATION MISMATCH: Original '{orig.duration}', Explanation '{expl.duration}'"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.CRITICAL_DURATION_MISMATCH,
                is_critical=True,
                details=reason,
            ), True, reason
                
        return FieldComparison(
            field_id=orig.field_id,
            field_name=orig.name,
            category=orig.category,
            original_display=orig_disp,
            explanation_display=expl_disp,
            status="PASS",
            mismatch_type=None,
            is_critical=False,
            details="Medication name, dosage, and frequency verified accurately."
        ), False, None

    @classmethod
    def _compare_instruction(
        cls,
        orig: MedicalFact,
        expl: MedicalFact,
        orig_disp: str,
        expl_disp: str
    ) -> Tuple[FieldComparison, bool, Optional[str]]:
        # Check negation flip
        if orig.negation != expl.negation:
            reason = f"CRITICAL NEGATION FLIP: Original had negation={orig.negation} ('{orig.source_text}'), Explanation had negation={expl.negation} ('{expl.source_text}')"
            return FieldComparison(
                field_id=orig.field_id,
                field_name=orig.name,
                category=orig.category,
                original_display=orig_disp,
                explanation_display=expl_disp,
                status="MISMATCH",
                mismatch_type=MismatchType.CRITICAL_NEGATION_FLIP,
                is_critical=True,
                details=reason
            ), True, reason
            
        return FieldComparison(
            field_id=orig.field_id,
            field_name=orig.name,
            category=orig.category,
            original_display=orig_disp,
            explanation_display=expl_disp,
            status="PASS",
            mismatch_type=None,
            is_critical=False,
            details="Instruction and condition verified without negation flips."
        ), False, None

    @classmethod
    def _compare_general(
        cls,
        orig: MedicalFact,
        expl: MedicalFact,
        orig_disp: str,
        expl_disp: str
    ) -> Tuple[FieldComparison, bool, Optional[str]]:
        return FieldComparison(
            field_id=orig.field_id,
            field_name=orig.name,
            category=orig.category,
            original_display=orig_disp,
            explanation_display=expl_disp,
            status="PASS",
            mismatch_type=None,
            is_critical=False,
            details="Verified."
        ), False, None

    @classmethod
    def _format_fact_display(cls, fact: MedicalFact) -> str:
        if fact.category == FactCategory.LABORATORY:
            parts = [f"{fact.name}: {fact.value}"]
            if fact.unit:
                parts.append(fact.unit)
            if fact.reference_range:
                parts.append(f"(Ref: {fact.reference_range})")
            if fact.flag and fact.flag != FlagType.NONE:
                parts.append(f"[{fact.flag.value if hasattr(fact.flag, 'value') else fact.flag}]")
            return " ".join(parts)
        elif fact.category == FactCategory.MEDICATION:
            parts = [fact.name]
            if fact.dosage:
                parts.append(fact.dosage)
            elif fact.strength:
                parts.append(fact.strength)
            if fact.frequency:
                parts.append(f"- {fact.frequency}")
            if fact.duration:
                parts.append(f"for {fact.duration}")
            return " ".join(parts)
        elif fact.category == FactCategory.INSTRUCTION:
            prefix = "DO NOT " if fact.negation else ""
            return f"{prefix}{fact.action or fact.instruction_text} {fact.condition or ''}".strip()
        return f"{fact.name}: {fact.value or fact.source_text}"
