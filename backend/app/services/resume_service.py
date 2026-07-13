"""
Resume CRUD service — database operations for resumes and ATS scores.
"""
from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging_config import get_logger, audit_logger
from app.database.models import Resume, ATSScore
from app.services import ml_service

logger = get_logger(__name__)


async def save_resume(
    db: AsyncSession,
    user_id: str,
    filename: str,
    content: bytes,
    ext: str,
    raw_text: str,
) -> Resume:
    """Save uploaded resume file to disk and database, generate embeddings."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{user_id}_{filename}")
    with open(file_path, "wb") as fh:
        fh.write(content)

    cleaned = ml_service.clean_resume(raw_text)
    embedding = ml_service.get_embedding(cleaned)
    experience_years = ml_service.extract_experience_years(raw_text)

    # Extract skills via keyword matching (enhanced in Batch 2 with NER)
    from app.core.roles import JOB_ROLES
    all_skills: set[str] = set()
    for role_data in JOB_ROLES.values():
        all_skills.update(role_data["skills"])
    found_skills = [s for s in all_skills if s.lower() in raw_text.lower()]

    resume = Resume(
        user_id=user_id,
        filename=filename,
        file_path=file_path,
        file_type=ext.lstrip("."),
        file_size_bytes=len(content),
        raw_text=raw_text,
        cleaned_text=cleaned,
        word_count=len(raw_text.split()),
        extracted_skills=found_skills,
        experience_years=experience_years,
        embedding_json=embedding,
    )
    db.add(resume)
    await db.flush()

    audit_logger.info("Resume saved: id=%s user=%s file=%s", resume.id, user_id, filename)
    return resume


async def save_ats_score(
    db: AsyncSession,
    user_id: str,
    resume_id: str,
    analysis: dict,
    job_id: Optional[str] = None,
) -> ATSScore:
    """Persist ATS analysis results to database."""
    ats = ATSScore(
        resume_id=resume_id,
        job_id=job_id,
        user_id=user_id,
        ml_score=analysis["ml_score"],
        skill_similarity=analysis["skill_similarity"],
        semantic_score=analysis["semantic_score"],
        ats_score=analysis["ats_score"],
        role_fit=analysis["role_fit"],
        hire_probability=analysis["hire_prob"],
        confidence=analysis["confidence"],
        decision=analysis["decision"],
        predicted_role=analysis.get("predicted_role"),
        top_roles=analysis["top_roles"],
        found_skills=analysis["found_skills"],
        missing_skills=analysis["missing_skills"],
        explanation=analysis["explanation"],
    )
    db.add(ats)
    await db.flush()
    audit_logger.info("ATS score saved: id=%s user=%s role_fit=%.1f", ats.id, user_id, ats.role_fit)
    return ats


async def get_user_resumes(db: AsyncSession, user_id: str) -> list[Resume]:
    """Retrieve all resumes for a given user, ordered by creation date."""
    result = await db.execute(
        select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
    )
    return list(result.scalars().all())


async def get_resume_by_id(db: AsyncSession, resume_id: str, user_id: str) -> Resume | None:
    """Retrieve a specific resume by ID, scoped to the owning user."""
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    )
    return result.scalar_one_or_none()
