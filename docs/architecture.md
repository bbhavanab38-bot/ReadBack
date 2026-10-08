# ReadBack: System Architecture

## 1. Overview
**ReadBack** is an AI-powered healthcare accessibility platform that translates complex medical documents into patient-friendly explanations with **independent field-level fidelity verification**.

The central technical innovation is:
> Rather than asking the same language model "Is this explanation correct?", ReadBack converts the source document into structured typed medical facts, generates an explanation, independently re-extracts facts from that explanation, compares them field-by-field against confirmed facts, and **blocks the explanation if medically critical information has changed**.

---

## 2. End-to-End System Architecture

```text
                         READBACK
                            │
                            ▼
                         USER
                            │
                            ▼
                    React Web Interface
                            │
                            ▼
                       FastAPI API
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
             OCR                    Document Parser
              │                           │
              └─────────────┬─────────────┘
                            ▼
                  Structured Fact Layer
                            │
                            ▼
                    User Confirmation
                            │
                            ▼
                     LLM Explanation
                            │
                            ▼
               Independent Fact Extraction
                            │
                            ▼
                   Verification Engine
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
              VERIFIED              BLOCKED
                 │                     │
                 ▼                     ▼
          Evidence + Next Step   Explain Mismatch
```

---

## 3. Core Architectural Components

### 3.1 OCR & Parsing Abstraction
- **PaddleOCR Provider**: Primary neural OCR for printed tabular documents and prescriptions.
- **Tesseract Fallback**: Secondary traditional OCR provider.
- **Simulated Provider**: Fallback for deterministic zero-dependency demo runs and synthetic test suites.
- All OCR providers output verbatim text along with line-level bounding boxes `[x_min, y_min, x_max, y_max]` to enable **source evidence highlighting**.

### 3.2 Structured Fact Layer
Medical information is converted into strongly-typed Pydantic schemas:
- **Laboratory Facts**: `name`, `value`, `unit`, `reference_range`, `flag` (`LOW`, `HIGH`, `NORMAL`, `CRITICAL`), `confidence`, `bbox`.
- **Medication Facts**: `name`, `strength`, `dosage`, `frequency`, `route`, `duration`, `confidence`, `bbox`.
- **Instruction Facts**: `action`, `negation` (`True`/`False`), `condition`, `timing`, `source_text`.
- **Verified Next Step**: `service_name`, `timing`, `source_text`, `is_explicit` (`True`/`False`).

### 3.3 User Confirmation Gate
- High-confidence fields ($\ge 80\%$) are staged for automatic approval.
- Low-confidence fields ($< 80\%$) or unparsed lines trigger an interactive warning badge, prompting user review before explanation generation.

### 3.4 Multilingual Explanation Engine
- Generates simple-language summaries in **English, Kannada (ಕನ್ನಡ), Hindi (हिन्दी), and Tamil (தமிழ்)**.
- Pluggable LLM provider abstraction:
  - `MockProvider`: Deterministic, zero-API-key runner with support for testing corruptions.
  - `OllamaProvider`: Local private on-premise execution (e.g., Llama 3 / Mistral).
  - `OpenAIProvider`: Cloud inference (`gpt-4o-mini`).

### 3.5 Independent Fact Extraction & Verification Engine
- Parses the generated explanation text *independently* to re-extract medical facts, numbers, units, drug names, and negation polarity.
- Runs field-by-field normalized matching:
  - Numeric check (equality tolerance $\le 0.001$).
  - Unit normalization (`g/dL`, `mg/dL`, `cells/µL`).
  - Drug name fuzzy/exact comparison.
  - Dosage and frequency normalization.
  - Negation flip detection (`Do NOT take` vs `Take`).
  - Abnormal flag consistency (`LOW` vs `NORMAL`).
- Status outcomes:
  - **VERIFIED**: 100% critical match, fidelity score $\ge 90\%$.
  - **PARTIALLY VERIFIED**: Minor non-critical fields unverified, fidelity score $\ge 80\%$.
  - **NEEDS REVIEW**: Low confidence fields present.
  - **BLOCKED**: Any critical mismatch. The unsafe explanation is gated and replaced with a prominent mismatch warning.

### 3.6 Verified Next Step
- Identifies healthcare services explicitly mentioned in the document (e.g., "Follow-up consultation after 2 weeks", "Repeat lipid profile in 3 months").
- Strictly refuses to recommend unstated specialists or tests.
