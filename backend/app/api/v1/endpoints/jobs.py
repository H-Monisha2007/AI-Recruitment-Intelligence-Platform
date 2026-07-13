"""
Phase 7 - Semantic Job Matching
Endpoint to match candidate resumes against job descriptions.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List

from app.auth.dependencies import get_current_active_user, require_recruiter
from app.database.models import User
from app.ml.vector_store import vector_store

router = APIRouter()

class JobMatchRequest(BaseModel):
    job_description: str = Field(..., description="The textual description of the job")
    top_k: int = Field(10, description="Number of top candidates to return")

class CandidateMatch(BaseModel):
    resume_id: str
    match_score: float
    metadata: dict

class JobMatchResponse(BaseModel):
    success: bool
    job_description_snippet: str
    matches: List[CandidateMatch]

@router.post("/match", response_model=JobMatchResponse, summary="Match candidates to a job description semantically", tags=["jobs"])
async def match_candidates_to_job(
    request: JobMatchRequest,
    current_user: User = Depends(require_recruiter)
):
    """
    Search across all parsed resume profiles in ChromaDB to find the 
    best semantically matching candidates.
    """
    results = vector_store.search_candidates(request.job_description, n_results=request.top_k)
    
    matches = []
    if results:
        for hit in results:
            # Distance in Chroma is 0 for identical, so we convert it to a 0-100 score roughly
            score = max(0.0, min(100.0, (1.0 - hit["distance"]) * 100))
            matches.append(
                CandidateMatch(
                    resume_id=hit["id"],
                    match_score=round(score, 1),
                    metadata=hit["metadata"]
                )
            )
            
    matches.sort(key=lambda x: x.match_score, reverse=True)
            
    return JobMatchResponse(
        success=True,
        job_description_snippet=request.job_description[:100] + "...",
        matches=matches
    )
