"""
Roles endpoint — returns the full job-role catalog.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_active_user
from app.database.models import User
from app.services.ml_service import get_all_job_roles

router = APIRouter()


@router.get("/", summary="List all supported job roles", tags=["roles"])
def get_roles(current_user: User = Depends(get_current_active_user)):
    roles = get_all_job_roles()
    return {
        "success": True,
        "total": len(roles),
        "roles": [
            {
                "name": name,
                "skills": data["skills"],
                "min_experience": data["exp"],
                "color": data["color"],
            }
            for name, data in roles.items()
        ],
    }