"""
Phase 8 - AI Career Guidance Module
Provides intelligent career paths and learning roadmaps based on resume.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Any
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.dependencies import get_current_active_user
from app.database.models import User, Resume, CareerRecommendation
from app.database.session import get_db
from app.ml.llm_service import ai_llm_service

router = APIRouter()

class CareerGuidanceResponse(BaseModel):
    success: bool
    recommended_roles: List[str]
    career_paths: List[str]
    skills_to_learn: List[str]
    certifications: List[str]
    learning_roadmap: dict
    ai_reasoning: str

@router.get("/guidance/{resume_id}", response_model=CareerGuidanceResponse, summary="Generate personalized career guidance", tags=["career"])
async def get_career_guidance(
    resume_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Uses the candidate's parsed resume to generate an LLM-powered 
    Career Roadmap and Path Recommendations.
    """
    # 1. Fetch resume
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id))
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    if not ai_llm_service.is_active:
        raise HTTPException(status_code=503, detail="AI Service is not configured (Missing GOOGLE_API_KEY)")
        
    # Check if we already have one cached
    result = await db.execute(select(CareerRecommendation).where(CareerRecommendation.resume_id == resume_id))
    existing = result.scalar_one_or_none()
    
    if existing:
        return CareerGuidanceResponse(
            success=True,
            recommended_roles=existing.recommended_roles,
            career_paths=existing.career_paths,
            skills_to_learn=existing.skills_to_learn,
            certifications=existing.certifications,
            learning_roadmap=existing.learning_roadmap,
            ai_reasoning=existing.ai_reasoning
        )
        
    # Generate new guidance
    prompt = f"""
    You are an expert AI Career Mentor. I will provide a candidate's resume summary.
    Generate a highly structured JSON response detailing optimal career paths in technology or AI.
    
    Schema MUST be:
    {{
       "recommended_roles": [],
       "career_paths": ["short description of path 1", "short description of path 2"],
       "skills_to_learn": [],
       "certifications": [],
       "learning_roadmap": {{
           "month_1": "focus area",
           "month_2": "focus area",
           "month_3": "focus area"
       }},
       "ai_reasoning": "A paragraph explaining why these are good recommendations based on the candidate's background."
    }}
    
    Candidate Background:
    Experience: {resume.experience_years} years
    Skills Found: {', '.join(resume.extracted_skills)}
    Clean Text Preview: {resume.cleaned_text[:3000]}
    """
    
    try:
        response_data = await ai_llm_service.generate_structured(
            system_prompt="You are an AI Career Mentor.",
            user_prompt=prompt
        )
        
        if "error" in response_data:
            raise HTTPException(status_code=500, detail="Failed to generate guidance.")
            
        # Save to DB
        rec = CareerRecommendation(
            resume_id=resume.id,
            user_id=current_user.id,
            recommended_roles=response_data.get("recommended_roles", []),
            career_paths=response_data.get("career_paths", []),
            skills_to_learn=response_data.get("skills_to_learn", []),
            certifications=response_data.get("certifications", []),
            learning_roadmap=response_data.get("learning_roadmap", {}),
            ai_reasoning=response_data.get("ai_reasoning", "")
        )
        db.add(rec)
        await db.commit()
        
        return CareerGuidanceResponse(
            success=True,
            recommended_roles=rec.recommended_roles,
            career_paths=rec.career_paths,
            skills_to_learn=rec.skills_to_learn,
            certifications=rec.certifications,
            learning_roadmap=rec.learning_roadmap,
            ai_reasoning=rec.ai_reasoning
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
