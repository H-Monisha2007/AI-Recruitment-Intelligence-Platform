"""
Background Celery task for heavy resume processing (embedding generation,
NER extraction, vector index updates).
"""
from app.tasks.celery_app import celery_app
from app.core.logging_config import get_logger
import asyncio

logger = get_logger(__name__)


@celery_app.task(name="process_resume_task", bind=True, max_retries=3)
def process_resume_task(self, resume_id: str):
    """
    Background task to:
    1. Parse PDF/DOCX text
    2. Clean and normalize text
    3. Extract skills using NER
    4. Generate embeddings
    5. Update vector store index
    6. Update database with results
    """
    logger.info("Starting background processing for resume: %s", resume_id)

    from app.database.session import AsyncSessionLocal

    async def _process():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from app.database.models import Resume
            from app.services.ml_service import (
                get_embedding,
                comprehensive_resume_review,
                extract_experience_years,
            )

            result = await db.execute(select(Resume).where(Resume.id == resume_id))
            resume = result.scalar_one_or_none()
            if resume is None:
                logger.error("Resume %s not found in database", resume_id)
                return

            # Generate embedding if not already present
            if resume.embedding_json is None and resume.cleaned_text:
                embedding = get_embedding(resume.cleaned_text)
                if embedding:
                    resume.embedding_json = embedding

            # Extract experience years if not set
            if resume.experience_years == 0 and resume.raw_text:
                resume.experience_years = extract_experience_years(resume.raw_text)

            await db.commit()
            logger.info("Background processing complete for resume: %s", resume_id)

    try:
        asyncio.run(_process())
        return {"status": "success", "resume_id": resume_id}
    except Exception as exc:
        logger.error("Failed to process resume %s: %s", resume_id, exc)
        raise self.retry(exc=exc, countdown=30)
