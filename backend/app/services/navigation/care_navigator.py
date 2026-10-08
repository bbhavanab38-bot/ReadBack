import re
from typing import Optional, List
from app.schemas.navigation import VerifiedNextStep
from app.schemas.facts import MedicalFact

class CareNavigator:
    """
    Verified Next Step Service
    Strictly grounds any follow-up healthcare recommendation in explicit text from the document.
    Refuses to infer or hypothesize any unstated service, specialist, or test.
    """

    EXPLICIT_TRIGGERS = [
        r'follow[- ]?up (?:consultation|visit|review)?(?:\s+(?:after|in|within)\s+([^.\n]+))?',
        r'review (?:after|in|within)\s+([^.\n]+)',
        r'consult (?:dr\.?|doctor|specialist|physician|cardiologist|endocrinologist|nephrologist|neurologist|ent)(?:\s+(?:after|in|within)\s+([^.\n]+))?',
        r'repeat (?:test|blood test|cbc|lipid profile|hba1c|lft|kft|tsh)(?:\s+(?:after|in|within)\s+([^.\n]+))?',
        r'next visit[:\s]+([^.\n]+)',
        r'recheck[:\s]+(?:after|in)\s+([^.\n]+)'
    ]

    @classmethod
    def extract_verified_next_step(
        cls,
        document_text: str,
        confirmed_facts: Optional[List[MedicalFact]] = None
    ) -> VerifiedNextStep:
        lines = [line.strip() for line in document_text.split('\n') if line.strip()]

        # Search for explicit instructions
        for line in lines:
            line_low = line.lower()
            
            # 1. Follow-up consultation
            match_fu = re.search(r'follow[- ]?up(?:\s+consultation|\s+visit|\s+review)?(?:\s+(?:after|in|within)\s+([^.,;\n]+))?', line_low)
            if match_fu:
                timing = match_fu.group(1).strip() if match_fu.group(1) else None
                follow_up_text = match_fu.group(0)
                if "consultation" in follow_up_text:
                    service_name = "Follow-up consultation"
                elif "visit" in follow_up_text:
                    service_name = "Follow-up visit"
                elif "review" in follow_up_text:
                    service_name = "Follow-up review"
                else:
                    service_name = "Follow-up"
                return VerifiedNextStep(
                    has_next_step=True,
                    service_name=service_name,
                    timing=timing,
                    department_or_specialty=None,
                    source_text=line,
                    page=1,
                    is_explicit=True,
                    verification_status="VERIFIED",
                    rationale="Explicit follow-up instruction identified in document."
                )

            # 2. Review after
            match_rev = re.search(r'review(?:\s+after|\s+in|\s+within)\s+([^.,;\n]+)', line_low)
            if match_rev:
                timing = match_rev.group(1).strip()
                return VerifiedNextStep(
                    has_next_step=True,
                    service_name="Clinical Review",
                    timing=timing,
                    department_or_specialty=None,
                    source_text=line,
                    page=1,
                    is_explicit=True,
                    verification_status="VERIFIED",
                    rationale="Explicit clinical review timeframe identified in document."
                )

            # 3. Repeat test
            match_rep = re.search(r'repeat\s+((?:blood\s+)?test|cbc|lipid profile|hba1c|lft|kft|tsh)(?:\s+(?:after|in|within)\s+([^.,;\n]+))?$', line_low)
            if match_rep:
                test_name = match_rep.group(1).strip().title()
                timing = match_rep.group(2).strip() if match_rep.group(2) else None
                return VerifiedNextStep(
                    has_next_step=True,
                    service_name=f"Repeat {test_name}",
                    timing=timing,
                    department_or_specialty=None,
                    source_text=line,
                    page=1,
                    is_explicit=True,
                    verification_status="VERIFIED",
                    rationale=f"Explicit order to repeat '{test_name}' found in document."
                )

            # 4. Specialist consultation explicitly mentioned
            match_spec = re.search(r'consult\s+([a-zA-Z\s]+?)(?:\s+(?:after|in|within)\s+([^.,;\n]+))?$', line_low)
            if match_spec:
                spec_name = match_spec.group(1).strip().title()
                timing = match_spec.group(2).strip() if match_spec.group(2) else None
                return VerifiedNextStep(
                    has_next_step=True,
                    service_name=f"Consultation: {spec_name}",
                    timing=timing,
                    department_or_specialty=spec_name,
                    source_text=line,
                    page=1,
                    is_explicit=True,
                    verification_status="VERIFIED",
                    rationale=f"Explicit referral to '{spec_name}' found in document."
                )

        # Strict boundary: No explicit instruction -> Refuse to infer
        return VerifiedNextStep(
            has_next_step=False,
            service_name=None,
            timing=None,
            department_or_specialty=None,
            source_text=None,
            page=None,
            is_explicit=False,
            verification_status="NO_EXPLICIT_INSTRUCTION",
            rationale="No explicit healthcare-service or follow-up instruction was found in this document. ReadBack does not infer unstated appointments."
        )
