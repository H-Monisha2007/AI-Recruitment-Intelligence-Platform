"""
Central API router — v1.
"""
from __future__ import annotations
from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics, auth, reports, resumes, roles, train, jobs, career
)

api_router = APIRouter()

api_router.include_router(auth.router,      prefix="/auth",      tags=["auth"])
api_router.include_router(resumes.router,   prefix="/resumes",   tags=["resumes"])
api_router.include_router(roles.router,     prefix="/roles",     tags=["roles"])
api_router.include_router(reports.router,   prefix="/reports",   tags=["reports"])
api_router.include_router(train.router,     prefix="/train",     tags=["train"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(jobs.router,      prefix="/jobs",      tags=["jobs"])
api_router.include_router(career.router,    prefix="/career",    tags=["career"])