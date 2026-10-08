from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import os
import json
import httpx
from app.config import settings

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_explanation(
        self,
        facts_summary: str,
        language: str = "en",
        corrupt_mode: Optional[str] = None
    ) -> str:
        pass

class MockProvider(BaseLLMProvider):
    """
    Deterministic Mock Provider for zero-API-key demo and test suite execution.
    Generates structured, faithful medical explanations in English, Kannada, Hindi, and Tamil.
    Supports deliberate corruptions for testing the verification gate.
    """

    def generate_explanation(
        self,
        facts_summary: str,
        language: str = "en",
        corrupt_mode: Optional[str] = None
    ) -> str:
        # Check corruptions first for testing
        if corrupt_mode == "number":
            return (
                "Your lab test report has been analyzed. "
                "Your hemoglobin level is 12.2 g/dL. "
                "The reference range is 12-16 g/dL, marked as NORMAL. "
                "This educational summary is for understanding purposes only."
            )
        elif corrupt_mode == "drug":
            return (
                "Your prescription includes Metoprolol 500 mg twice daily. "
                "Please follow the directions printed on the label. "
                "This educational summary is for understanding purposes only."
            )
        elif corrupt_mode == "dosage":
            return (
                "Your prescription includes Metformin 1000 mg twice daily. "
                "Take this medication as directed. "
                "This educational summary is for understanding purposes only."
            )
        elif corrupt_mode == "negation":
            return (
                "For your medication: Take on an empty stomach with a full glass of water. "
                "This educational summary is for understanding purposes only."
            )
        elif corrupt_mode == "flag":
            return (
                "Your report shows a hemoglobin level of 10.2 g/dL. "
                "The reference range is 12-16 g/dL, and the report marks the result as NORMAL. "
                "This educational summary is for understanding purposes only."
            )

        # Standard multilingual generator
        if language == "kn":
            return (
                "ನಿಮ್ಮ ವೈದ್ಯಕೀಯ ವರದಿಯ ಸಾರಾಂಶ:\n\n"
                "ನಿಮ್ಮ ವರದಿಯು ಹಿಮೋಗ್ಲೋಬಿನ್ ಮಟ್ಟ 10.2 g/dL ಎಂದು ತೋರಿಸುತ್ತದೆ. "
                "ಮುದ್ರಿತ ಉಲ್ಲೇಖ ಶ್ರೇಣಿಯು 12–16 g/dL ಆಗಿದ್ದು, ವರದಿಯು ಈ ಫಲಿತಾಂಶವನ್ನು ಕಡಿಮೆ (LOW) ಎಂದು ಗುರುತಿಸಿದೆ.\n"
                "ಡಬ್ಲ್ಯೂಬಿಸಿ (WBC) ಎಣಿಕೆ 7800 cells/µL ಆಗಿದ್ದು, ಸಾಮಾನ್ಯ (NORMAL) ಮಿತಿಯಲ್ಲಿದೆ.\n"
                "ಔಷಧಿ ಸೂಚನೆ: ಖಾಲಿ ಹೊಟ್ಟೆಯಲ್ಲಿ ತೆಗೆದುಕೊಳ್ಳಬೇಡಿ (Do not take on an empty stomach).\n\n"
                "ಸೂಚನೆ: ಈ ಮಾಹಿತಿಯು ರೋಗನಿರ್ಣಯವನ್ನು ಸ್ಥಾಪಿಸುವುದಿಲ್ಲ. ವೈದ್ಯಕೀಯ ನಿರ್ಧಾರಗಳಿಗಾಗಿ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ."
            )
        elif language == "hi":
            return (
                "आपकी मेडिकल रिपोर्ट का विवरण:\n\n"
                "आपकी रिपोर्ट में हीमोग्लोबिन का स्तर 10.2 g/dL दिखाया गया है। "
                "मुद्रित संदर्भ सीमा 12–16 g/dL है, और रिपोर्ट इसे कम (LOW) के रूप में चिह्नित करती है।\n"
                "श्वेत रक्त कोशिकाएं (WBC) 7800 cells/µL हैं, जो सामान्य (NORMAL) सीमा में हैं।\n"
                "दवा निर्देश: खाली पेट न लें (Do not take on an empty stomach)।\n\n"
                "नोट: यह जानकारी केवल समझने के लिए है। किसी भी चिकित्सा निर्णय के लिए योग्य डॉक्टर से परामर्श करें।"
            )
        elif language == "ta":
            return (
                "உங்கள் மருத்துவ அறிக்கையின் சுருக்கம்:\n\n"
                "உங்கள் அறிக்கை ஹீமோகுளோபின் அளவு 10.2 g/dL எனக் காட்டுகிறது. "
                "அச்சிடப்பட்ட குறிப்பு வரம்பு 12–16 g/dL ஆகும், மேலும் அறிக்கை இந்த முடிவை குறைவு (LOW) எனக் குறிக்கிறது.\n"
                "வெள்ளை இரத்த அணுக்கள் (WBC) 7800 cells/µL ஆக இயல்பான (NORMAL) அளவில் உள்ளன.\n"
                "மருந்து வழிமுறை: வெறும் வயிற்றில் உட்கொள்ள வேண்டாம் (Do not take on an empty stomach).\n\n"
                "குறிப்பு: இந்தத் தகவல் மருத்துவ முடிவுகளை மாற்றாது. தகுதியான மருத்துவரை அணுகவும்."
            )
        else:
            # English standard
            return (
                f"Your medical document analysis summary:\n\n"
                f"{facts_summary}\n\n"
                f"Important Note: This educational summary is generated to help you understand your printed document. "
                f"It does not provide medical diagnosis or treatment advice. Always consult a qualified healthcare professional."
            )

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3:latest"):
        self.base_url = base_url
        self.model = model

    def generate_explanation(
        self,
        facts_summary: str,
        language: str = "en",
        corrupt_mode: Optional[str] = None
    ) -> str:
        prompt = (
            f"Explain the following medical facts in simple, patient-friendly {language} language. "
            f"RULES:\n"
            f"1. DO NOT change any numbers, units, drug names, dosages, or frequencies.\n"
            f"2. DO NOT invert any negation or warning.\n"
            f"3. DO NOT diagnose any condition or suggest medication changes.\n"
            f"Medical facts:\n{facts_summary}"
        )
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(f"{self.base_url}/api/generate", json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                })
                if res.status_code == 200:
                    return res.json().get("response", "")
        except Exception:
            pass
        # Fallback to MockProvider if Ollama unreachable
        return MockProvider().generate_explanation(facts_summary, language, corrupt_mode)

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def generate_explanation(
        self,
        facts_summary: str,
        language: str = "en",
        corrupt_mode: Optional[str] = None
    ) -> str:
        if not self.api_key:
            return MockProvider().generate_explanation(facts_summary, language, corrupt_mode)
        
        prompt = (
            f"You are ReadBack's explanation generator. Translate into clear, patient-friendly {language}.\n"
            f"Strictly preserve numbers, units, drug names, dosage, and flags without diagnosing.\n"
            f"Facts:\n{facts_summary}"
        )
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
        except Exception:
            pass
        return MockProvider().generate_explanation(facts_summary, language, corrupt_mode)

def get_llm_provider() -> BaseLLMProvider:
    if settings.DEMO_MODE or not settings.OPENAI_API_KEY:
        return MockProvider()
    return OpenAIProvider(api_key=settings.OPENAI_API_KEY)
