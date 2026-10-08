import re
from typing import Tuple, Dict, Any, List

class SafetyGuardrails:
    """
    ReadBack Safety Engine & Guardrails
    Enforces strict safety boundaries:
    - Rejects diagnosis and prescription requests
    - Detects emergency medical conditions
    - Protects against prompt injections in document text
    - Redacts potential PII
    """

    PROMPT_INJECTION_PATTERNS = [
        r'ignore\s+(?:all\s+)?previous\s+instructions',
        r'disregard\s+(?:all\s+)?prior\s+prompts',
        r'you\s+are\s+now\s+a\s+different',
        r'system\s*:\s*',
        r'override\s+(?:safety|system)\s+rules',
        r'developer\s+mode'
    ]

    EMERGENCY_KEYWORDS = [
        r'severe\s+chest\s+pain',
        r'shortness\s+of\s+breath',
        r'difficulty\s+breathing',
        r'sudden\s+weakness',
        r'facial\s+droop',
        r'loss\s+of\s+consciousness',
        r'coughing\s+up\s+blood',
        r'anaphylaxis',
        r'stroke\s+symptoms'
    ]

    DIAGNOSIS_REQUEST_PATTERNS = [
        r'do\s+i\s+have\b',
        r'diagnose\s+me',
        r'what\s+disease\s+is\s+this',
        r'is\s+this\s+cancer',
        r'what\s+illness\s+do\s+i\s+have'
    ]

    TREATMENT_CHANGE_PATTERNS = [
        r'should\s+i\s+stop\s+(?:taking\s+)?',
        r'can\s+i\s+double\s+(?:the\s+)?(?:dose|dosage)',
        r'should\s+i\s+increase\s+(?:the\s+)?(?:dose|dosage)',
        r'should\s+i\s+decrease\s+(?:the\s+)?(?:dose|dosage)',
        r'what\s+medicine\s+should\s+i\s+take',
        r'recommend\s+a\s+treatment'
    ]

    @classmethod
    def sanitize_untrusted_text(cls, text: str) -> str:
        """
        Strips potential prompt injections and normalizes untrusted input.
        Never executes text as system instructions.
        """
        sanitized = text
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "[FILTERED_UNTRUSTED_INSTRUCTION]", sanitized, flags=re.IGNORECASE)
        return sanitized

    @classmethod
    def check_emergency(cls, text: str) -> Tuple[bool, str]:
        text_lower = text.lower()
        for kw in cls.EMERGENCY_KEYWORDS:
            if re.search(kw, text_lower):
                return True, (
                    "⚠️ URGENT HEALTH NOTICE: This information may require prompt professional attention. "
                    "If you believe you are experiencing a medical emergency, contact your local emergency service "
                    "(e.g., 911 / 112 / 108) or seek immediate professional medical care."
                )
        return False, ""

    @classmethod
    def validate_safety(cls, query_or_text: str) -> Tuple[bool, str]:
        text_lower = query_or_text.lower()
        
        # Check emergency first
        is_em, em_msg = cls.check_emergency(text_lower)
        if is_em:
            return False, em_msg

        # Check diagnosis request
        for p in cls.DIAGNOSIS_REQUEST_PATTERNS:
            if re.search(p, text_lower):
                return False, (
                    "I can help you understand what the document says, but I cannot diagnose a condition "
                    "or interpret your health status. Please consult a qualified healthcare professional."
                )

        # Check treatment/medication change request
        for p in cls.TREATMENT_CHANGE_PATTERNS:
            if re.search(p, text_lower):
                return False, (
                    "I can help you understand what the document says, but I cannot recommend medication changes, "
                    "dosage adjustments, or treatment plans. Please consult a qualified healthcare professional."
                )

        return True, ""

    @classmethod
    def redact_pii(cls, text: str) -> str:
        # Simple regex redaction for phone numbers, emails, and SSN/MRN patterns
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', '[REDACTED_EMAIL]', text)
        text = re.sub(r'\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b', '[REDACTED_PHONE]', text)
        text = re.sub(r'\b(?:MRN|SSN|Aadhaar|ID)[:\s]+[A-Za-z0-9-]+\b', '[REDACTED_ID]', text, flags=re.IGNORECASE)
        return text
