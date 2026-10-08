import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models.database import engine, Base, SessionLocal
from app.models.models import DocumentModel
from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.extraction import router as extraction_router
from app.api.explanation import router as explanation_router
from app.api.verification import router as verification_router
from app.api.navigation import router as navigation_router
from app.api.evaluation import router as evaluation_router
from app.services.evaluation.dataset_generator import SyntheticDatasetGenerator
from app.services.upload_cleanup import cleanup_orphaned_uploads

logger = logging.getLogger(__name__)

# Initialize database schemas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ReadBack API",
    description="Medical Document Understanding, Field-Level Fidelity Verification & Verified Care Navigation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API routers under /api or root
app.include_router(health_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(extraction_router, prefix="/api")
app.include_router(explanation_router, prefix="/api")
app.include_router(verification_router, prefix="/api")
app.include_router(navigation_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")

# Also include directly at root for prompt compliance
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(extraction_router)
app.include_router(explanation_router)
app.include_router(verification_router)
app.include_router(navigation_router)
app.include_router(evaluation_router)

@app.on_event("startup")
def on_startup():
    # 1. Verify synthetic dataset exists
    master_path = "./data/generated/master_dataset.json"
    if not os.path.exists(master_path):
        print("[ReadBack] Generating master synthetic dataset (100+ documents)...")
        SyntheticDatasetGenerator.generate_all()

    # 2. Seed initial demo documents if database empty
    db = SessionLocal()
    try:
        count = db.query(DocumentModel).count()
        if count == 0:
            print("[ReadBack] Seeding initial demonstration documents...")
            from app.api.documents import DEMO_DOCUMENTS
            from app.services.extraction.parser import DocumentFactParser
            from app.services.navigation.care_navigator import CareNavigator
            from app.services.extraction.explainer import ExplanationEngine
            from app.services.extraction.independent_extractor import IndependentExtractor
            from app.services.verification.engine import VerificationEngine
            from app.schemas.facts import MedicalFact

            # Seed 1: Verified Blood Report
            demo1 = DEMO_DOCUMENTS["lab_report"]
            res1 = DocumentFactParser.parse_document_text(demo1["content"], document_type="lab_report")
            facts1 = res1.facts
            ns1 = CareNavigator.extract_verified_next_step(demo1["content"], facts1)
            expl1 = ExplanationEngine.generate_explanation("seed_1", facts1, language="en")
            ind1 = IndependentExtractor.extract_from_explanation(expl1.explanation_text, facts1)
            ver1 = VerificationEngine.verify(facts1, ind1)

            doc1 = DocumentModel(
                id="demo_cbc_001",
                filename="Blood Report (CBC).txt",
                file_type="text/plain",
                file_size=len(demo1["content"]),
                document_type="lab_report",
                page_count=1,
                ocr_quality=0.98,
                raw_text=demo1["content"],
                extracted_facts=[f.dict() for f in facts1],
                confirmed_facts=[f.dict() for f in facts1],
                selected_language="en",
                explanation_text=expl1.explanation_text,
                independent_facts=[f.dict() for f in ind1],
                verification_result=ver1.dict(),
                next_step=ns1.dict()
            )
            db.add(doc1)

            # Seed 2: Blocked Mismatch Lab Report
            demo2 = DEMO_DOCUMENTS["corrupted_test"]
            res2 = DocumentFactParser.parse_document_text(demo2["content"], document_type="lab_report")
            facts2 = res2.facts
            expl2_corrupt = (
                "Your lab test report has been analyzed. "
                "Your hemoglobin level is 12.2 g/dL. "
                "The reference range is 12-16 g/dL, marked as LOW."
            )
            ind2 = IndependentExtractor.extract_from_explanation(expl2_corrupt, facts2)
            ver2 = VerificationEngine.verify(facts2, ind2)
            ns2 = CareNavigator.extract_verified_next_step(demo2["content"], facts2)

            doc2 = DocumentModel(
                id="demo_blocked_002",
                filename="Lab Report (Numeric Hallucination).txt",
                file_type="text/plain",
                file_size=len(demo2["content"]),
                document_type="lab_report",
                page_count=1,
                ocr_quality=0.95,
                raw_text=demo2["content"],
                extracted_facts=[f.dict() for f in facts2],
                confirmed_facts=[f.dict() for f in facts2],
                selected_language="en",
                explanation_text=expl2_corrupt,
                independent_facts=[f.dict() for f in ind2],
                verification_result=ver2.dict(),
                next_step=ns2.dict()
            )
            db.add(doc2)

            # Seed 3: Prescription with Verified Review
            demo3 = DEMO_DOCUMENTS["prescription"]
            res3 = DocumentFactParser.parse_document_text(demo3["content"], document_type="prescription")
            facts3 = res3.facts
            ns3 = CareNavigator.extract_verified_next_step(demo3["content"], facts3)
            expl3 = ExplanationEngine.generate_explanation("seed_3", facts3, language="en")
            ind3 = IndependentExtractor.extract_from_explanation(expl3.explanation_text, facts3)
            ver3 = VerificationEngine.verify(facts3, ind3)

            doc3 = DocumentModel(
                id="demo_rx_003",
                filename="Outpatient Prescription.txt",
                file_type="text/plain",
                file_size=len(demo3["content"]),
                document_type="prescription",
                page_count=1,
                ocr_quality=0.96,
                raw_text=demo3["content"],
                extracted_facts=[f.dict() for f in facts3],
                confirmed_facts=[f.dict() for f in facts3],
                selected_language="en",
                explanation_text=expl3.explanation_text,
                independent_facts=[f.dict() for f in ind3],
                verification_result=ver3.dict(),
                next_step=ns3.dict()
            )
            db.add(doc3)

            db.commit()
            print("[ReadBack] Initial documents successfully seeded.")
    except Exception as e:
        print(f"[ReadBack] Seed initialization warning: {e}")
    finally:
        db.close()

    cleanup_db = SessionLocal()
    try:
        referenced_paths = [
            file_path
            for (file_path,) in cleanup_db.query(DocumentModel.file_path).all()
            if file_path
        ]
        removed, failures = cleanup_orphaned_uploads(settings.UPLOAD_DIR, referenced_paths)
        logger.info(
            "Upload cleanup complete: removed=%s failures=%s",
            removed,
            failures,
        )
    except Exception:
        logger.exception("Upload cleanup skipped because active document references could not be read")
    finally:
        cleanup_db.close()
