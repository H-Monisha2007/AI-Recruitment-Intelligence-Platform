"""
Resume endpoints — upload, analyse, list, skill-gap.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.database.models import User
from app.database.session import get_db
from app.schemas import (
    ResumeAnalysisResponse,
    ResumeReviewData,
    RoleData,
    ExplanationData,
    ResumeUploadResponse,
    SkillGapRequest,
    SkillGapResponse,
)
from app.services import file_service, ml_service, resume_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ── Upload only ───────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a resume (without analysis)",
    tags=["resumes"],
)
async def upload_resume(
    file: UploadFile = File(..., description="PDF, DOCX, or TXT resume file"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    content, ext = await file_service.read_upload(file)
    raw_text = file_service._extract_from_bytes(content, ext)
    if not raw_text.strip():
        return JSONResponse(
            status_code=422,
            content={"success": False, "error": "Could not extract text from the uploaded file."},
        )

    saved = await resume_service.save_resume(
        db, current_user.id, file.filename or "resume", content, ext, raw_text
    )

    return ResumeUploadResponse(
        success=True,
        resume_id=saved.id,
        filename=saved.filename,
        word_count=saved.word_count,
        extracted_skills=saved.extracted_skills,
        experience_years=saved.experience_years,
    )


# ── Upload + Analyse ───────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=ResumeAnalysisResponse,
    summary="Upload and fully analyse a resume against a target role",
    tags=["resumes"],
)
async def analyze_resume(
    file: UploadFile = File(...),
    selected_role: str = Form(..., description="Target job role (e.g. 'ML Engineer')"),
    save_result: bool = Form(default=True, description="Persist ATS score to database"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    content, ext = await file_service.read_upload(file)
    raw_text = file_service._extract_from_bytes(content, ext)
    if not raw_text.strip():
        return JSONResponse(
            status_code=422,
            content={"success": False, "error": "Cannot read resume. Try another format."},
        )

    from app.core.utils import clean_resume
    from app.core.roles import JOB_ROLES
    from app.agents.coordinator import run_coordinator_pipeline

    cleaned = clean_resume(raw_text)
    role_data = JOB_ROLES.get(selected_role, JOB_ROLES["Software Engineer"])
    
    # Run the new Multi-Agent Coordinator!
    try:
        analysis = await run_coordinator_pipeline(
            resume_text=cleaned,
            job_role=selected_role,
            job_profile=role_data
        )
        
        # Merge parsed skills back so the response looks complete
        if "parsed_resume" in analysis and "skills" in analysis["parsed_resume"]:
            skills_dict = analysis["parsed_resume"]["skills"]
            analysis["found_skills"] = (
                skills_dict.get("languages", []) +
                skills_dict.get("frameworks", []) +
                skills_dict.get("tools", [])
            )
            analysis["missing_skills"] = list(set(role_data["skills"]) - set(analysis["found_skills"]))
            
    except Exception as e:
        logger.error("Coordinator agent failed, using procedural fallback: %s", e)
        analysis = ml_service.analyze_resume(cleaned, selected_role)

    ats_score_id: Optional[str] = None
    if save_result:
        saved_resume = await resume_service.save_resume(
            db, current_user.id, file.filename or "resume", content, ext, raw_text
        )
        ats_obj = await resume_service.save_ats_score(db, current_user.id, saved_resume.id, analysis)
        ats_score_id = ats_obj.id

    return ResumeAnalysisResponse(
        success=True,
        ats_score_id=ats_score_id,
        ml_score=analysis["ml_score"],
        skill_similarity=analysis["skill_similarity"],
        semantic_score=analysis["semantic_score"],
        ats_score=analysis["ats_score"],
        role_fit=analysis["role_fit"],
        experience=analysis["experience"],
        role=analysis["role"],
        top_roles=analysis["top_roles"],
        role_data=RoleData(**analysis["role_data"]),
        resume_preview=analysis["resume_preview"],
        full_resume=analysis["full_resume"],
        predicted_role=analysis.get("predicted_role"),
        model_confidence=analysis.get("model_confidence"),
        top3_preds=analysis["top3_preds"],
        resume_review=ResumeReviewData(**analysis["resume_review"]),
        found_skills=analysis["found_skills"],
        missing_skills=analysis["missing_skills"],
        hire_prob=analysis["hire_prob"],
        confidence=analysis["confidence"],
        decision=analysis["decision"],
        explanation=ExplanationData(**analysis["explanation"]),
    )


# ── Skill gap ─────────────────────────────────────────────────────────────────

@router.post(
    "/skill-gap",
    response_model=SkillGapResponse,
    summary="Analyse skill gap between resume text and a list of required skills",
    tags=["resumes"],
)
async def skill_gap_analysis(
    payload: SkillGapRequest,
    current_user: User = Depends(get_current_active_user),
):
    found, missing, coverage = ml_service.skill_match_score(payload.resume_text, payload.job_skills)
    recommendations = [f"Study and obtain experience in: {s}" for s in missing[:5]]
    return SkillGapResponse(
        success=True,
        found_skills=found,
        missing_skills=missing,
        coverage_percent=round(coverage, 2),
        recommendations=recommendations,
    )


# ── List user resumes ─────────────────────────────────────────────────────────

@router.get(
    "/",
    summary="List resumes for the authenticated user",
    tags=["resumes"],
)
async def list_resumes(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    resumes = await resume_service.get_user_resumes(db, current_user.id)
    return {
        "success": True,
        "total": len(resumes),
        "resumes": [
            {
                "id": r.id,
                "filename": r.filename,
                "word_count": r.word_count,
                "experience_years": r.experience_years,
                "created_at": r.created_at.isoformat(),
            }
            for r in resumes
        ],
    }
