"""
SQLAlchemy ORM Models — Enterprise AI Recruitment Intelligence Platform.

Models:
    User, CandidateProfile, Skill, JobRole, Resume, Analysis, ATSScore,
    AuditLog, TrainingHistory, CareerRecommendation, LearningRoadmap
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# Association Tables for Many-to-Many Relationships
# ═══════════════════════════════════════════════════════════════════════════════

resume_skills = Table(
    "resume_skills",
    Base.metadata,
    Column("resume_id", String(36), ForeignKey("resumes.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

job_skills = Table(
    "job_skills",
    Base.metadata,
    Column("job_id", String(36), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


# ═══════════════════════════════════════════════════════════════════════════════
# Users & Auth
# ═══════════════════════════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="candidate")
    # Roles: "admin", "recruiter", "hiring_manager", "candidate"

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_profile: Mapped[Optional["CandidateProfile"]] = relationship("CandidateProfile", back_populates="user", uselist=False)
    resumes: Mapped[list["Resume"]] = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")
    ats_scores: Mapped[list["ATSScore"]] = relationship("ATSScore", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"


# ═══════════════════════════════════════════════════════════════════════════════
# Candidate Profile
# ═══════════════════════════════════════════════════════════════════════════════

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linked_in_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    education_level: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="candidate_profile")

    def __repr__(self) -> str:
        return f"<CandidateProfile {self.user_id}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Skills
# ═══════════════════════════════════════════════════════════════════════════════

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="general")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def __repr__(self) -> str:
        return f"<Skill {self.name}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Job Roles
# ═══════════════════════════════════════════════════════════════════════════════

class JobRole(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    min_experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    salary_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Many-to-Many with Skills
    skills: Mapped[list["Skill"]] = relationship("Skill", secondary=job_skills)
    analyses: Mapped[list["Analysis"]] = relationship("Analysis", back_populates="job")

    def __repr__(self) -> str:
        return f"<JobRole {self.title}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Resumes
# ═══════════════════════════════════════════════════════════════════════════════

class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cleaned_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Extracted structured data
    extracted_skills: Mapped[list] = mapped_column(JSON, default=list)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    structured_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Vector Embedding (serialized for DB storage)
    embedding_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resumes")
    skills: Mapped[list["Skill"]] = relationship("Skill", secondary=resume_skills)
    analyses: Mapped[list["Analysis"]] = relationship("Analysis", back_populates="resume", cascade="all, delete-orphan")
    ats_scores: Mapped[list["ATSScore"]] = relationship("ATSScore", back_populates="resume", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Resume {self.filename} for {self.user_id}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis (Semantic Analysis Results)
# ═══════════════════════════════════════════════════════════════════════════════

class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[Optional[str]] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)

    # Quantitative Scores
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    skill_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    experience_score: Mapped[float] = mapped_column(Float, default=0.0)
    semantic_similarity: Mapped[float] = mapped_column(Float, default=0.0)

    # AI Predictions & Insights
    predicted_role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    top_matching_roles: Mapped[list] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, default=list)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    recommendations: Mapped[list] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(String(50), default="completed")  # processing, completed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="analyses")
    job: Mapped[Optional["JobRole"]] = relationship("JobRole", back_populates="analyses")

    def __repr__(self) -> str:
        return f"<Analysis id={self.id} score={self.overall_score}>"


# ═══════════════════════════════════════════════════════════════════════════════
# ATS Score — Detailed scoring record per resume-role evaluation
# ═══════════════════════════════════════════════════════════════════════════════

class ATSScore(Base):
    __tablename__ = "ats_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[Optional[str]] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)

    # Core Scores (0-100)
    ml_score: Mapped[float] = mapped_column(Float, default=0.0)
    skill_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    semantic_score: Mapped[float] = mapped_column(Float, default=0.0)
    ats_score: Mapped[float] = mapped_column(Float, default=0.0)
    role_fit: Mapped[float] = mapped_column(Float, default=0.0)

    # AI Decision
    hire_probability: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    decision: Mapped[str] = mapped_column(String(100), default="PENDING")

    # Predictions
    predicted_role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    top_roles: Mapped[list] = mapped_column(JSON, default=list)
    found_skills: Mapped[list] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="ats_scores")
    user: Mapped["User"] = relationship("User", back_populates="ats_scores")

    def __repr__(self) -> str:
        return f"<ATSScore id={self.id} role_fit={self.role_fit} decision={self.decision}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Audit Logs
# ═══════════════════════════════════════════════════════════════════════════════

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_id}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Training History
# ═══════════════════════════════════════════════════════════════════════════════

class TrainingHistory(Base):
    __tablename__ = "training_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # { "accuracy": 0.92, "f1": 0.91, "precision": 0.90, "total_samples": 5000 }

    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    dataset_info: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def __repr__(self) -> str:
        return f"<TrainingHistory {self.model_name} v{self.version}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Career Recommendation
# ═══════════════════════════════════════════════════════════════════════════════

class CareerRecommendation(Base):
    __tablename__ = "career_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    recommended_roles: Mapped[list] = mapped_column(JSON, default=list)
    career_paths: Mapped[list] = mapped_column(JSON, default=list)
    skills_to_learn: Mapped[list] = mapped_column(JSON, default=list)
    certifications: Mapped[list] = mapped_column(JSON, default=list)
    learning_roadmap: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_reasoning: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def __repr__(self) -> str:
        return f"<CareerRecommendation id={self.id} user={self.user_id}>"
