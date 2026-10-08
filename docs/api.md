# ReadBack: REST API Documentation

The ReadBack API is implemented with **FastAPI** and documented via interactive Swagger UI at `/docs` and ReDoc at `/redoc`.

---

## Endpoints Summary

### System Health
```http
GET /health
```
Returns system status, active LLM provider, OCR engine, and supported languages.

---

### Document Ingestion & Upload
```http
POST /documents/upload
```
Uploads a medical document (PDF, PNG, JPG, or TXT) or loads a pre-configured synthetic demo document.
- Multipart Form Fields:
  - `file`: Uploaded file (optional if `demo_type` is supplied).
  - `demo_type`: `"lab_report"` | `"prescription"` | `"edge_case"` (optional).
- Response: `DocumentDetail` object with extracted facts and OCR quality metrics.

---

### Retrieve Document
```http
GET /documents/{id}
```
Fetches document details, confirmed facts, current explanation, verification results, and verified next step.

---

### Extract Structured Facts
```http
POST /documents/{id}/extract
```
Re-runs OCR and structured fact parsing on the uploaded document.

---

### Confirm / Edit Extracted Facts
```http
POST /documents/{id}/confirm
```
Submits user-confirmed or manually-edited facts before explanation generation.
- Request Body:
```json
{
  "confirmed_facts": [
    {
      "field_id": "lab_001",
      "category": "laboratory",
      "name": "Hemoglobin",
      "value": 10.2,
      "unit": "g/dL",
      "reference_range": "12.0 - 16.0",
      "flag": "LOW",
      "source_text": "Hemoglobin 10.2 g/dL LOW",
      "confidence": 0.98,
      "user_confirmed": true
    }
  ]
}
```

---

### Generate Explanation
```http
POST /documents/{id}/explain
```
Generates patient-friendly explanations in the selected language.
- Request Body:
```json
{
  "language": "en",  // "en", "kn", "hi", "ta"
  "corrupt_for_testing": null // Optional: "number", "drug", "dosage", "negation", "flag"
}
```

---

### Run Field-Level Verification
```http
POST /documents/{id}/verify
```
Executes independent fact extraction on the generated explanation and performs field-by-field normalized comparison against confirmed facts.
- Response:
```json
{
  "overall_status": "VERIFIED", // "VERIFIED", "PARTIALLY_VERIFIED", "NEEDS_REVIEW", "BLOCKED"
  "fidelity_score": 100.0,
  "total_fields_checked": 4,
  "passed_count": 4,
  "review_count": 0,
  "critical_mismatches_count": 0,
  "field_comparisons": [...],
  "explanation_safe_to_display": true
}
```

---

### Verified Next Step
```http
GET /documents/{id}/next-step
```
Extracts explicit follow-up instructions (or returns `NO_EXPLICIT_INSTRUCTION`).

```http
POST /documents/{id}/provider
```
Saves provider contact details for follow-up coordination.

---

### Multi-Document Comparison & Timeline
```http
POST /documents/compare
```
Compares multiple documents and flags conflicting dosages or instructions.

```http
GET /documents/timeline
```
Retrieves chronological values for key laboratory metrics over time.

---

### Evaluation & Research Benchmark
```http
POST /evaluation/run
```
Executes full benchmark evaluation across synthetic dataset comparing Baseline vs ReadBack.

```http
GET /evaluation/results
```
Retrieves the most recent benchmark run metrics.
