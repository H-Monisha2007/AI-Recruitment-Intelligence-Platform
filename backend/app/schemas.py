"""
Pydantic v2 schemas — request/response models for every API surface.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional, Union

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ============================================================================
# Shared / utility
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


# ============================================================================
# Auth
# ============================================================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(default="candidate", pattern="^(admin|recruiter|candidate)$")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Resume
# ============================================================================

class ResumeUploadResponse(BaseModel):
    success: bool
    resume_id: str
    filename: str
    word_count: int
    extracted_skills: List[str]
    experience_years: int
    message: str = "Resume uploaded and parsed successfully"


class ResumeReviewData(BaseModel):
    sections_found: List[str]
    has_contact: bool
    action_verbs: int
    has_quant: bool
    word_count: int
    length_status: str
    tech_stack: List[str]
    has_github: bool
    has_portfolio: bool


class RoleData(BaseModel):
    skills: List[str]
    exp: int
    color: str


class ExplanationData(BaseModel):
    selected_reasons: List[str]
    rejected_reasons: List[str]
    matched_skills: List[str]
    missing_skills: List[str]


class ResumeAnalysisResponse(BaseModel):
    success: bool
    ats_score_id: Optional[str] = None
    ml_score: float
    skill_similarity: float
    semantic_score: float
    ats_score: float
    role_fit: float
    experience: int
    role: str
    top_roles: List[List[Union[str, float]]]
    role_data: RoleData
    resume_preview: str
    full_resume: str
    predicted_role: Optional[str] = None
    model_confidence: Optional[float] = None
    top3_preds: List[List[Union[str, float]]]
    resume_review: ResumeReviewData
    found_skills: List[str]
    missing_skills: List[str]
    hire_prob: float
    confidence: float
    decision: str
    explanation: ExplanationData




# ============================================================================
# Skill Gap Analysis
# ============================================================================

class SkillGapRequest(BaseModel):
    resume_text: str = Field(min_length=50)
    job_skills: List[str] = Field(min_length=1)


class SkillGapResponse(BaseModel):
    success: bool
    found_skills: List[str]
    missing_skills: List[str]
    coverage_percent: float
    recommendations: List[str]




# ============================================================================
# ML Training
# ============================================================================

class TrainMetrics(BaseModel):
    Model: str
    Accuracy: str
    Precision: str
    Recall: str
    F1_Score: str


class TrainResponse(BaseModel):
    success: bool
    message: str
    metrics: List[TrainMetrics]
    best_model: str
    training_time_seconds: Optional[float] = None


# ============================================================================
# Reports
# ============================================================================

class PDFReportRequest(BaseModel):
    ats_score_id: Optional[str] = None
    role: str
    role_fit: float
    ml_score: float
    skill_similarity: float
    semantic_score: float = 0.0
    ats_score: float
    experience: int
    top_roles: List[List[Any]]
    found_skills: List[str] = []
    missing_skills: List[str] = []
    decision: str = ""
    hire_prob: float = 0.0


# ============================================================================
# Analytics / Dashboard
# ============================================================================

class DashboardStatsResponse(BaseModel):
    total_resumes_analyzed: int
    total_users: int
    avg_role_fit: float
    avg_ats_score: float
    top_roles_distribution: List[dict]
    decisions_breakdown: dict
    recent_analyses: List[dict]
