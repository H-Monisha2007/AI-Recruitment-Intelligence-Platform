"""
Analytics / Dashboard endpoint — Recruiter intelligence metrics.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_recruiter
from app.database.models import ATSScore, Resume, User
from app.database.session import get_db
from app.schemas import DashboardStatsResponse

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStatsResponse, summary="Dashboard statistics for recruiters", tags=["analytics"])
async def get_dashboard_stats(
    current_user: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    total_resumes = await db.scalar(select(func.count(Resume.id))) or 0
    total_users = await db.scalar(select(func.count(User.id))) or 0
    avg_role_fit = await db.scalar(select(func.avg(ATSScore.role_fit))) or 0.0
    avg_ats = await db.scalar(select(func.avg(ATSScore.ats_score))) or 0.0

    # Decisions breakdown
    decision_rows = await db.execute(
        select(ATSScore.decision, func.count(ATSScore.id)).group_by(ATSScore.decision)
    )
    decisions = {row[0]: row[1] for row in decision_rows}

    # Top roles distribution
    role_rows = await db.execute(
        select(ATSScore.predicted_role, func.count(ATSScore.id))
        .where(ATSScore.predicted_role.isnot(None))
        .group_by(ATSScore.predicted_role)
        .order_by(func.count(ATSScore.id).desc())
        .limit(10)
    )
    top_roles = [{"role": row[0], "count": row[1]} for row in role_rows]

    # Recent 10 analyses
    recent_rows = await db.execute(
        select(ATSScore, User.full_name, User.email)
        .join(User, ATSScore.user_id == User.id)
        .order_by(ATSScore.created_at.desc())
        .limit(10)
    )
    recent = [
        {
            "candidate": row[1],
            "email": row[2],
            "role_fit": round(row[0].role_fit, 1),
            "decision": row[0].decision,
            "ats_score": round(row[0].ats_score, 1),
            "created_at": row[0].created_at.isoformat(),
        }
        for row in recent_rows
    ]

    return DashboardStatsResponse(
        total_resumes_analyzed=total_resumes,
        total_users=total_users,
        avg_role_fit=round(float(avg_role_fit), 1),
        avg_ats_score=round(float(avg_ats), 1),
        top_roles_distribution=top_roles,
        decisions_breakdown=decisions,
        recent_analyses=recent,
    )